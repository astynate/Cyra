from cyra_model.tokenizer import CyraTokenizer
from cyra_model.transformer import TransformerBlock
from cyra_model.positional_encoding import PositionalEncoding
from keras import mixed_precision
from keras.layers import Input, Dense, Embedding, Dropout, BatchNormalization, Flatten, LayerNormalization
from keras.optimizers import Adam
from keras.models import Model
import numpy as np
import tensorflow as tf

mixed_precision.set_global_policy('mixed_float16')

custom_objects = {
    'PositionEncoding': PositionalEncoding,
    'TransformerBlock': TransformerBlock
}

class Cyra:
    def __init__(self, tokenizer, transformer_block_counter, embedding_dim, num_heads, feed_forward_dim) -> None:
        self.tokenizer = tokenizer
        self.initializer = tf.initializers.GlorotUniform()

        self.inputs = Input(shape=(self.tokenizer.sequence_length,))

        self.embedding = Embedding(input_dim=self.tokenizer.get_dimension(), output_dim=embedding_dim, embeddings_initializer=self.initializer)(self.inputs)
        self.pos_encoding = PositionalEncoding(embedding_dim, embedding_dim)(self.embedding)

        self.transformer_block = TransformerBlock(embedding_dim, num_heads, feed_forward_dim, kernel_initializer=self.initializer)(self.pos_encoding)
        self.transformer_block = LayerNormalization()(self.transformer_block)
        # self.transformer_block = Dropout(0.1)(self.transformer_block)

        for _ in range(transformer_block_counter - 1):
            self.transformer_block = TransformerBlock(embedding_dim, num_heads, feed_forward_dim, kernel_initializer=self.initializer)(self.transformer_block)
            self.transformer_block = LayerNormalization()(self.transformer_block)
            # self.transformer_block = Dropout(0.1)(self.transformer_block)

        self.transformer_block = Flatten()(self.transformer_block)
        self.outputs = Dense(self.tokenizer.get_dimension(), activation='sigmoid', kernel_initializer=self.initializer)(self.transformer_block)
        self.model = Model(inputs=self.inputs, outputs=self.outputs)
        self.model.compile(optimizer=Adam(), loss='categorical_crossentropy', metrics=['accuracy'])

        print(f'Input shape: {self.inputs.shape}')
        print(f'Ouput shape: {self.outputs.shape}')
        print(f'Cyra model was created, count params: {self.model.count_params()}')

    def __call__(self, text: str) -> str:
        tokens = self.tokenizer.get_sequence(text)
        tokens = np.array(tokens).reshape(1, 50)
        
        predicted_label = self.model.predict(np.array(tokens))
        predicted_word = self.tokenizer.get_text([[np.argmax(predicted_label[0])]][0])

        return predicted_word

if __name__ == '__main__':
    
    cyra_tokenizer_path = 'D:/Exider Company/Cyra/trained-models/cyra_tokenizer.pickle'
    cyra_tokenizer = CyraTokenizer(cyra_tokenizer_path, 50)

    cyra_model = Cyra(cyra_tokenizer, 12, 1024, 16, 1024)