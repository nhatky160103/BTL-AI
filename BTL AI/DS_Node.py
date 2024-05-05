from DS_Street import list_pho

mapsize = 750
rate = mapsize / float(2928)

class Node:
    def __init__(self, ten_dinh_nut, vi_tri_x, vi_tri_y, danh_sach_duong):
        self.ten_dinh_nut = ten_dinh_nut
        self.vi_tri_x = vi_tri_x
        self.vi_tri_y = vi_tri_y
        self.danh_sach_duong = danh_sach_duong
    def getNodeName(self):
        return self.ten_dinh_nut
    def getLocationX(self):
        return self.vi_tri_x
    def getLocationY(self):
        return self.vi_tri_y
    def getListStreets(self):
        return self.danh_sach_duong
    
def changeCoor(x1, x2):
    x = round(x1*rate)
    y = mapsize - round(x2*rate)
    return x, y  

# Đọc file và xử lý dữ liệu thành danh sách Node
danh_sach_node = []
with open('BTL AI\Toan\Danh_Sach_Nut.txt', 'r', encoding="utf-8") as file:
    for line in file:
        if "***" in line:
            break

        data = line.strip().split()
        danh_sach_duong = []
        
        for i in range(3, len(data)):
            danh_sach_duong.append(list_pho[int(data[i])])
        
        x1, x2 = changeCoor(int(data[1]), int(data[2]))
        
        nodee = Node(int(data[0]), x1, x2, danh_sach_duong)
        
        danh_sach_node.append(nodee)
