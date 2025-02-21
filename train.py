from __future__ import print_function
import os
import argparse
import datetime
import random
import torch
import logging
import torch.nn as nn
import torch.backends.cudnn as cudnn
from utils.common import *

from trainfiles.trainer_dp import Trainer

from torch.utils.tensorboard import SummaryWriter
cudnn.benchmark = True


def save_checkpoint(state, is_best, filename='checkpoint.pth'):
    torch.save(state, os.path.join(opt.outf,filename))
    if is_best:
        torch.save(state, os.path.join(opt.outf,'model_best.pth'))
        
        
'''  Main Function to train the model'''
def main(opt):
    # load the training loss scheme
    train_round =1
    epoches = [70]
    
    trainer = Trainer(lr=opt.lr,backbone=int(opt.backbone),devices=opt.devices,
                      datapath=opt.datapath,trainlist=opt.trainlist,
                      vallist=opt.vallist,batch_size=opt.batch_size,
                      test_size=opt.test_batch,pretrain=opt.pretrain)
    

    
    # validate the pretrained model on test data
    best_ACC = -10
    best_index = 0
    summary_writer = SummaryWriter(opt.save_logdir)
    start_epoch = opt.startEpoch 

    if trainer.is_pretrain:
        pass
        # best_EPE = trainer.validate(summary_writer=summary_writer,epoch=start_epoch)

    iterations = 0
    
    for r in range(opt.startRound, train_round):
        
        end_epoch = epoches[r]

        logger.info('round %d'%r)
        logger.info('num of epoches: %d' % end_epoch)
        logger.info('\t'.join(['epoch', 'time_stamp', 'train_loss', 'train_EPE', 'EPE', 'lr']))
        
        for i in range(start_epoch, end_epoch):
            #val_EPE = trainer.validate(summary_writer,i)
            avg_loss, avg_acc,iterations = trainer.train_one_epoch(i, r,iterations,summary_writer)
            val_acc = trainer.validate(summary_writer,i)
            is_best = best_ACC < 0 or val_acc > best_ACC

            if is_best:
                best_EPE = val_acc
                best_index = i
            
      
            save_checkpoint({
                'round': r + 1,
                'epoch': i + 1,
                'arch': 'dispnet',
                'state_dict': trainer.get_model(),
                'best_EPE': best_EPE,
            }, is_best, '%s_%d_%d_%.3f.pth' % (opt.net, r, i, val_acc))
        
            logger.info('Validation[epoch:%d]: '%i+'\t'.join([datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), str(avg_loss), 
                                                              str(avg_acc), str(val_acc), str(trainer.current_lr)]))
            logger.info("max acc from %d epoch" % (best_index))
        
        start_epoch = 0



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--net', type=str, help='indicates the name of net', default='simplenet')
    parser.add_argument('--workers', type=int, help='number of data loading workers', default=8)
    parser.add_argument('--batch_size', type=int, default=8, help='input batch size')
    parser.add_argument('--test_batch', type=int, default=4, help='test batch size')
    parser.add_argument('--lr', type=float, default=0.0002, help='learning rate, default=0.0002')
    parser.add_argument('--cuda', action='store_true', help='enables, cuda')
    parser.add_argument('--devices', type=str, help='indicates CUDA devices, e.g. 0,1,2', default='0')
    parser.add_argument('--outf', default='.', help='folder to output images and model checkpoints')
    parser.add_argument('--manualSeed', type=int, help='manual seed')
    parser.add_argument('--backbone', type=str, help='model for finetuning', default='')
    parser.add_argument('--startRound', type=int, help='the round number to start training, useful of lr scheduler', default='0')
    parser.add_argument('--startEpoch', type=int, help='the epoch number to start training, useful of lr scheduler', default='0')
    parser.add_argument('--logFile', type=str, help='logging file', default='./train.log')
    parser.add_argument('--showFreq', type=int, help='display frequency', default='100')
    parser.add_argument('--datapath', type=str, help='provide the root path of the data', default='/spyder/sceneflow/')
    parser.add_argument('--trainlist', type=str, help='provide the train file (with file list)', default='FlyingThings3D_release_TRAIN.list')
    parser.add_argument('--vallist', type=str, help='provide the val file (with file list)', default='FlyingThings3D_release_TEST.list')
    parser.add_argument('--save_logdir',type=str,help='tensorboard log files saved path',default='experiments_logdirs')
    parser.add_argument('--pretrain',type=str,help='Load pretrain model for fine-tuning',default='None')
    opt = parser.parse_args()


    try:
        os.makedirs(opt.outf)
    except OSError:
        pass
    hdlr = logging.FileHandler(opt.logFile)
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr) 
    logger.info('Configurations: %s', opt)
    
    if opt.manualSeed is None:
        opt.manualSeed = random.randint(1, 10000)
    logger.info("Random Seed: %s", opt.manualSeed)
    random.seed(opt.manualSeed)
    torch.manual_seed(opt.manualSeed)
    if opt.cuda:
        torch.cuda.manual_seed_all(opt.manualSeed)

    if torch.cuda.is_available() and not opt.cuda:
        logger.warning("WARNING: You should run with --cuda since you have a CUDA device.")
    main(opt)

