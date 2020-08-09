import argparse
import logging
import os
import sys
import time

sys.path.append("..")
sys.path.append("../../common")

from tqdm import tqdm
from code_search.twin.twin_train import load_examples
from common.metrices import metrics

import torch
from transformers import BertConfig
from common.models import TBertT
from common.utils import MODEL_FNAME, results_to_df


def get_eval_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data_dir", default="../data/code_search_net/python", type=str,
        help="The input data dir. Should contain the .json files for the task.")
    parser.add_argument("--model_path", default=None, help="The model to evaluate")
    parser.add_argument("--no_cuda", action="store_true", help="Whether not to use CUDA when available")
    parser.add_argument("--test_num", type=int,
                        help="The number of true links used for evaluation. The retrival task is build around the true links")
    parser.add_argument("--per_gpu_eval_batch_size", default=8, type=int, help="Batch size per GPU/CPU for evaluation.")
    parser.add_argument("--output_dir", default="./evaluation/test", help="directory to store the results")
    parser.add_argument("--overwrite", action="store_true", help="overwrite the cached data")
    parser.add_argument("--code_bert", default="microsoft/codebert-base", help="the base bert")
    parser.add_argument("--exp_name", help="id for this run of experiment")
    args = parser.parse_args()
    args.output_dir = os.path.join(args.output_dir, args.exp_name)
    return args


def test(args, model, eval_examples, batch_size=1000):
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
    retr_res_path = os.path.join(args.output_dir, "raw_result.csv")

    cache_file = "cached_twin_test.dat"
    if args.overwrite or not os.path.isfile(cache_file):
        retrival_dataloader = eval_examples.get_chunked_retrivial_task_examples(batch_size)
        torch.save(retrival_dataloader, cache_file)
    else:
        retrival_dataloader = torch.load(cache_file)

    res = []
    for batch in tqdm(retrival_dataloader, desc="retrival evaluation"):
        nl_ids = batch[0]
        pl_ids = batch[1]
        labels = batch[2]
        nl_embd, pl_embd = eval_examples.id_pair_to_embd_pair(nl_ids, pl_ids)

        with torch.no_grad():
            model.eval()
            nl_embd = nl_embd.to(model.device)
            pl_embd = pl_embd.to(model.device)
            sim_score = model.get_sim_score(text_hidden=nl_embd, code_hidden=pl_embd)
            for n, p, prd, lb in zip(nl_ids.tolist(), pl_ids.tolist(), sim_score, labels.tolist()):
                res.append((n, p, prd, lb))

    df = results_to_df(res)
    df.to_csv(retr_res_path)
    m = metrics(df, output_dir=args.output_dir)
    return m


if __name__ == "__main__":
    args = get_eval_args()

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")
    res_file = os.path.join(args.output_dir, "./raw_res.csv")

    cache_dir = os.path.join(args.data_dir, "cache")
    cached_file = os.path.join(cache_dir, "test_examples_cache.dat".format())

    logging.basicConfig(level='INFO')
    logger = logging.getLogger(__name__)

    if not os.path.isdir(args.output_dir):
        os.mkdir(args.output_dir)

    model = TBertT(BertConfig(), args.code_bert)
    if args.model_path and os.path.exists(args.model_path):
        model_path = os.path.join(args.model_path, MODEL_FNAME)
        model.load_state_dict(torch.load(model_path))

    logger.info("model loaded")
    start_time = time.time()
    test_examples = load_examples(args.data_dir, data_type="test", model=model, overwrite=args.overwrite,
                                  num_limit=args.test_num)
    test_examples.update_embd(model)
    m = test(args, model, test_examples)
    exe_time = time.time() - start_time
    m.write_summary(exe_time)
    logger.info("finished test")
