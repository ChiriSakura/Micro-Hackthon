import os
import argparse
import torch
from transformers import AutoTokenizer
from models.bloom_modeling import BloomForCausalLM
from dataUtil import perplexity

# os.environ['CUDA_VISIBLE_DEVICES'] = '0'

def main(model_name_or_path, dataset, max_seq_len, max_samples=None):
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)
        tokenizer.pad_token = tokenizer.eos_token

        model = BloomForCausalLM.from_pretrained(
            model_name_or_path,
            torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            pad_token_id=tokenizer.pad_token_id,
        )
        model.config.pad_token_id = tokenizer.pad_token_id
        model.generation_config.pad_token_id = tokenizer.pad_token_id

        ppl = perplexity(model, tokenizer, max_seq_len, dataset, max_samples=max_samples)
        print(f'Perplexity on {dataset}: {ppl.item()}')

    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Calculate perplexity of a Bloom model on a dataset.")
    parser.add_argument("--model_name_or_path", type=str, default="bigscience/bloom-7b1",
                        help="Hugging Face model name or local path.")
    parser.add_argument("--dataset", type=str, default="wiki",
                        choices=["wiki", "c4", "ptb"],
                        help="Dataset to evaluate perplexity on.")
    parser.add_argument("--max_seq_len", type=int, default=2048,
                        help="Maximum sequence length.")
    parser.add_argument("--max_samples", type=int, default=None,
                        help="Optional number of complete sequences to evaluate.")

    args = parser.parse_args()

    main(args.model_name_or_path, args.dataset, args.max_seq_len, args.max_samples)
