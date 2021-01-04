#!/bin/csh
#$ -l gpu_card=1
#$ -q gpu     # Specify queue (use ‘debug’ for development)
#$ -N rnn_t_ke      # trace train single + post + online

module load python/3.7.3
module load pytorch/1.1.0

set root = "/afs/crc.nd.edu/user/j/jlin6/projects/ICSE2020/trace/trace_rnn"
cd $root

source "/afs/crc.nd.edu/user/j/jlin6/projects/ICSE2020/venv/bin/activate.csh"
#pip3 install -r /afs/crc.nd.edu/user/j/jlin6/projects/ICSE2020/requirement.txt


python train_trace_rnn.py \
--data_dir ../data/git_data/keras-team/keras \
--output_dir ./output \
--embd_file_path ./we/glove.6B.300d.txt \
--exp_name keras \
--valid_step 100 \
--logging_steps 10 \
--gradient_accumulation_steps 8 \
--per_gpu_eval_batch_size 8 \
--num_train_epoch 100 \
--is_embd_trainable \
--hidden_dim 256 \
--rnn_type bi_gru

#python train_trace_single.py \
#--data_dir ../data/git_data/dbcli/pgcli \
#--model_path ../pretrained_model/single_online_34000 \
#--output_dir ./output \
#--per_gpu_train_batch_size 4 \
#--per_gpu_eval_batch_size 4 \
#--logging_steps 50 \
#--save_steps 2000 \
#--gradient_accumulation_steps 16 \
#--num_train_epochs 400 \
#--learning_rate 4e-5 \
#--valid_step 2000 \
#--neg_sampling online
