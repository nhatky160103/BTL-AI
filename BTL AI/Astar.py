import math
import queue
from Xu_Ly_Danh_Sach_Dinh_Ke import matran_dinhke
from DS_Node import danh_sach_node


class Node:
    def __init__(self, index, g, h):
        self.index = index
        self.g = g
        self.h = h
        self.f = g + h

    def __lt__(self, orther):
        return self.f < orther.f


def Astar(matran_dinhke, danh_sach_node, start, goal):
    result = []
    n = len(danh_sach_node)
    b = [0.0] * 100
    distance = [[0.0] * n for _ in range(n)]

    for j in range(n):
        b[j] = math.sqrt((danh_sach_node[j].vi_tri_x - danh_sach_node[goal].vi_tri_x)
                         ** 2 + (danh_sach_node[j].vi_tri_y - danh_sach_node[goal].vi_tri_y) ** 2)

    for i in range(n):
        for j in range(n):
            distance[i][j] = 0
            if matran_dinhke[i][j] != -2:
                if(i!=0 or j !=2):
                    distance[i][j] = math.sqrt((danh_sach_node[i].vi_tri_x - danh_sach_node[j].vi_tri_x) ** 2 + (
                        danh_sach_node[i].vi_tri_y - danh_sach_node[j].vi_tri_y) ** 2)
                else:
                    distance[i][j] = math.sqrt((danh_sach_node[i].vi_tri_x - danh_sach_node[j].vi_tri_x) ** 2 + (
                        danh_sach_node[i].vi_tri_y - danh_sach_node[j].vi_tri_y) ** 2)*2+ 100
    
    trace = {}
    diem = [Node(i, 0, b[i]) for i in range(n)]
    Open = queue.PriorityQueue()
    Close = []
    diem[start].g = 0
    Open.put(diem[start])

    while not Open.empty():

        curnode = Open.get()
        Close.append(curnode.index)

        if curnode.index == goal:

            u = curnode.index

            while u != start:
                result.append(u)
                u = trace[u]
            result.append(u)
            result.reverse()
            return result

        for i in range(n):
            if matran_dinhke[curnode.index][i] != -2  :
                if i not in Close :
                    k =0
                    neibor = Node(i,curnode.g+distance[curnode.index][i],b[i])
                    for no in Open.queue:
                        if no.index == i: 
                            if no.f > neibor.f : 
                                no.g = neibor.g
                                no.h = neibor.h
                                no.f = neibor.f
                                trace[no.index] = curnode.index
                                k=1
                    if(k==0):
                        Open.put(neibor)
                        trace[neibor.index] = curnode.index
                
                    
                   
