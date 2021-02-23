import torch.nn as nn
from nbdt.model import SoftTreeSupLoss

def SoftTreeLoss_wrapper(data_cfg):
    '''
    Creates SoftTreeSupLoss wrapper for our dataset from the nbdt package
    
    returns:
    criterion - SoftTreeSupLoss
    '''
    criterion = nn.CrossEntropyLoss()
    criterion = SoftTreeSupLoss(
        dataset = data_cfg['dataset'],
        hierarchy='induced-densenet121',
        path_graph = os.path.join(data_cfg['hierarchyPath'], data_cfg['hierarchyJSON']),
        path_wnids = data_cfg[wnidPath],
        criterion = criterion
    )
    
    return criterion