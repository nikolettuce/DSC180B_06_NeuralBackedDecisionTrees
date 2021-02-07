# import custom modules
import sys
sys.path.insert(0, "src/util")
sys.path.insert(0, "src/model")
sys.path.insert(0, "src/data_util")

#import for build.sh
import subprocess

# imports for model
import torch
import torchvision
import os
import torch.optim as optim
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.checkpoint as cp
from torchvision import datasets, models, transforms
from sklearn.metrics import f1_score

from baseline import *

from nbdt.model import SoftNBDT
from nbdt.loss import SoftTreeSupLoss

from wn_utils import *
from graph import *
from dir_grab import *
from hierarchy import *
from debug_data import *

from datetime import datetime

def main(targets):
    '''
    runs project code based on targets
    
    configure filepaths based on data-params.json
    
    targets:
    data - builds data from build.sh, will run if no model folder is found.
    train - checks if data target has been run, runs model to train
    test - checks if data/train have been run, then creates induced hierarchy
    '''
    
    if 'data' in targets:
        print('---> Running data target...')
        with open('config/data-params.json') as fh:
            data_cfg = json.load(fh)
            print('---> loaded data config')
        
        # check for directory's existence and rename, raise if no directory exists
        DATA_DIR = data_cfg['dataDir']
        if os.path.isdir(os.path.join(DATA_DIR, 'train')): # default name after extraction
            os.rename(
                os.path.join(DATA_DIR, 'train'),
                os.path.join(DATA_DIR, 'train_snakes_r1')
            )
        elif not os.path.isdir(os.path.join(DATA_DIR, 'train')) | os.path.isdir(os.path.join(DATA_DIR, 'train_snakes_r1')):
            raise Exception('Please run build.sh before running run.py')
        
        # important name variables
        TRAIN_DIR = os.path.join(DATA_DIR, 'train_snakes_r1')
        VALID_DIR = os.path.join(DATA_DIR, 'valid_snakes_r1') # new dir to be made
        train_pct = 0.8
        
        # delete corrupted data from download
        delete_corrupted(TRAIN_DIR)

        # create validation set
        create_validation_set(DATA_DIR, TRAIN_DIR, VALID_DIR, train_pct)
        
        print("---> Finished running data target.")
        
    if 'train' in targets:
        print('---> Running train target...')
        
        with open('config/data-params.json') as fh:
            data_cfg = json.load(fh)
            print('---> loaded data config')
            
        with open('config/model-params.json') as fh:
            model_cfg = json.load(fh)
            print('---> loaded model config')
        
        # create dataloaders
        dataloaders_dict, num_classes = create_dataloaders(
            data_cfg['dataDir'],
            model_cfg['batchSize'],
            model_cfg['inputSize']
        )
        
        # Detect if we have a GPU available
        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        
        # Initialize the model for this run
        model_ft, input_size = initialize_model(
            model_cfg['modelName'],
            num_classes,
            feature_extract = model_cfg['featureExtract'],
            use_pretrained=True
        )
        
        model_ft = model_ft.to(device) # make model use GPU
        
        params_update = params_to_update(model_ft, model_cfg['featureExtract'])
        
        # Optimizer
        optimizer_ft = optim.Adam(params_update, lr=model_cfg['lr'])
        
        # Loss function
        criterion = nn.CrossEntropyLoss()
        
        # train model
        model_ft, loss_train, acc_train, fs_train, loss_val, acc_val, fs_val = train_model(
            model_ft,
            dataloaders_dict,
            criterion,
            optimizer = optimizer_ft,
            num_epochs = model_cfg['nEpochs'])
        
        # save model to model states in params
        now = datetime.now().strftime("%d/%m/%Y_%H:%M")
        model_path = os.path.join(data_cfg['dataDir'], "model_states")
        model_name = os.path.join(
            model_path, 
            "{}_{}_{}.pth".format(
                now,
                model_cfg['nEpochs'],
                model_cfg['modelName']
            )
        )
        if not os.path.isdir(model_path): # make sure model path is made
            os.mkdir(model_path)
            
        torch.save(model_ft.state_dict(), model_name)
        # write performance to data/model_logs
        write_model_to_json(
            loss_train,
            acc_train,
            fs_train,
            loss_val,
            acc_val,
            fs_val,
            n_epochs = model_cfg['nEpochs'],
            model_name = model_cfg['modelName'],
            fp = model_cfg['performancePath']
        )
        
        print("---> Finished running train target.")
        
        
if __name__ == '__main__':
    targets = sys.argv[1:]
    main(targets)