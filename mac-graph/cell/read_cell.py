
import tensorflow as tf

from ..util import *

from ..attention import *


def read_from_kb(args, features, vocab_embedding, in_all, noun="node"):
	"""Perform attention based read from table

	@param W_score is for testing/debug purposes so you can easily inject the score fn you'd like. The code will default to a variable normally
	
	@returns read_data
	"""

	with tf.name_scope(f"read_{noun}_from_kb"):

		# --------------------------------------------------------------------------
		# Constants and validations
		# --------------------------------------------------------------------------

		kb = features[f"kb_{noun}s"]
		kb_width = args[f"kb_{noun}_width"]
		kb_full_width = kb_width * args["embed_width"]

		d_kb_len = tf.shape(kb)[1]
		assert kb.shape[-1] == kb_width

		# --------------------------------------------------------------------------
		# Embed graph tokens
		# --------------------------------------------------------------------------
		
		emb_kb = tf.nn.embedding_lookup(vocab_embedding, kb)
		emb_kb = dynamic_assert_shape(emb_kb, 
			[features["d_batch_size"], d_kb_len, kb_width, args["embed_width"]])

		emb_kb = tf.reshape(emb_kb, [-1, d_kb_len, kb_full_width])

		# --------------------------------------------------------------------------
		# Generate mask and query
		# --------------------------------------------------------------------------
		
		query = tf.layers.dense(in_all, kb_full_width, activation=tf.nn.tanh)
		mask  = tf.layers.dense(in_all, kb_full_width, activation=tf.nn.tanh)

		# --------------------------------------------------------------------------
		# Do lookup via attention
		# --------------------------------------------------------------------------

		output = attention(emb_kb, query, mask)
		output = dynamic_assert_shape(output, [features["d_batch_size"], kb_full_width])
		return output



def read_cell(args, features, in_memory_state, in_control_state, vocab_embedding):
	"""
	A read cell

	@returns read_data

	"""


	with tf.name_scope("read_cell"):

		# --------------------------------------------------------------------------
		# Read data
		# --------------------------------------------------------------------------

		# We may run the network with no control cell
		if in_control_state is not None:
			in_all = tf.concat([in_memory_state, in_control_state], -1)
		else:
			in_all = in_memory_state

		reads = []

		if args["use_kb_nodes"]:
			reads.append(read_from_kb(args, features, vocab_embedding, in_all, "node"))

		if args["use_kb_edges"]:
			reads.append(read_from_kb(args, features, vocab_embedding, in_all, "edge"))

		read_data = tf.concat(reads, -1)

		# --------------------------------------------------------------------------
		# Shrink results
		# --------------------------------------------------------------------------

		read_data = tf.layers.dense(read_data, args["memory_width"], name="data_read_shrink", activation=tf.nn.tanh)
		
		read_data = dynamic_assert_shape(read_data, 
			[features["d_batch_size"], args["memory_width"]])

		return read_data




