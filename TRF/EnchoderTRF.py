import torch
import torch.nn as nn
import torch.nn.functional as F

class Embeadings(nn.Module):
    def __init__(self, vec_size, embedDim,numPosEmbeading):
        super().__init__()
        self.MLP = nn.Sequential(
            nn.Linear(vec_size, embedDim),
            nn.GELU(),
            nn.Linear(embedDim, embedDim * 4),
            nn.GELU(),
            nn.Linear(embedDim * 4 , embedDim),
        )
        self.posEMB = nn.Embedding(numPosEmbeading,embedDim)
    def forward(self, emb, pos = None):
        if pos == None:
            temp = torch.arange(emb.shape[1])
            pos = temp.unsqueeze(0).expand(emb.shape[0], -1).to(emb.device)
        # print(pos.shape)
        return self.MLP(emb) + self.posEMB(pos)

class EncoderBLock(nn.Module):
    def __init__(self, embedDim, num_heads, dropout = 0.1):
        super().__init__()
        self.embedDim = int(int(embedDim / num_heads) * num_heads)
        self.Attantion = nn.MultiheadAttention(self.embedDim, num_heads, dropout= dropout, batch_first= True)
        self.MLP = nn.Sequential(
            nn.Linear(self.embedDim, self.embedDim * 4),
            nn.GELU(),
            nn.Linear(self.embedDim * 4, self.embedDim)
        )
        self.Norm1 = nn.LayerNorm(self.embedDim)
        self.Norm2 = nn.LayerNorm(self.embedDim)
        self.Drop = nn.Dropout(dropout,inplace=True)
    def forward(self, inp, mask = None):
        a_o, _ = self.Attantion.forward(inp, inp , inp, key_padding_mask=mask)
        # print(len(a_o))
        l1 = self.Norm1(inp + self.Drop(a_o))
        m_o = self.MLP(l1)
        op = self.Norm2(m_o + l1)
        return op

class NextPred(nn.Module):
    def __init__(self, embedDim : int, idx = 0):
        super().__init__()
        self.idx = idx
        self.MLP = nn.Sequential(
            nn.Linear(embedDim, embedDim),
            nn.GELU(),
            nn.LayerNorm(embedDim),
            nn.Linear(embedDim, 2)
        )
    def forward(self, seq):
        return self.MLP(seq)


class EncoderOnly(nn.Module):
    def __init__(self, vecSize, embedDim = 10, numHeads = 2, numLayers = 6, numPosEmbeading=10, numSegEmbeading = 0, padIdx = 0):
        super().__init__()
        embedDim = int(int(embedDim / numHeads) * numHeads)
        self.cfgDict = {"vocabSize" : vecSize,
                        "embedDim" : embedDim,
                        "numHeads" : numHeads,
                        'numLayers' : numLayers,
                        "numPosEmbeading" : numPosEmbeading,
                        "numSegEmbeading" : numSegEmbeading,
                        }
        self.Embead = Embeadings(vecSize, embedDim, numPosEmbeading)
        self.Blocks = nn.ModuleList()
        for i in range(numLayers):
            self.Blocks.append(EncoderBLock(embedDim, numHeads))

        self.NSP = NextPred(embedDim)
    def forward(self, tokens):
        x = self.Embead.forward(tokens)
        for Block in self.Blocks:
            x = Block.forward(x)

        NSPOut = self.NSP.forward(x)
        return NSPOut

