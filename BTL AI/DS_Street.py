mapsize = 750
rate = mapsize / float(2928)

class Street:
    def __init__(self, ten_pho, danh_sach_dia_diem, id):
        self.ten_pho = ten_pho
        self.danh_sach_dia_diem = danh_sach_dia_diem
        self.id = id

class Destinations:
    def __init__(self, ten_dia_diem, vi_tri_x, vi_tri_y, address, danh_sach_dinh_ke, thuoc_pho):
        self.ten_dia_diem = ten_dia_diem
        self.vi_tri_x = vi_tri_x
        self.vi_tri_y = vi_tri_y
        self.address = address
        self.danh_sach_dinh_ke = danh_sach_dinh_ke
        self.thuoc_pho = thuoc_pho

def changeCoor(x1, x2):
    x = round(x1*rate)
    y = mapsize - round(x2*rate)
    return x, y  

list_pho = []
id = 0
with open('BTL AI\Toan\Danh_Sach_Pho.txt', 'r', encoding='utf-8') as file:
    for line in file:
        line = line.strip()
        if line == '***':
            break
        danh_sach_dia_diem = []
        s1 = Street(line, danh_sach_dia_diem, id)
        
        list_pho.append(s1)
        
        id += 1

data = []
# Doc file Dia diem
with open('BTL AI\Toan\Data_DiaDiem.txt', 'r', encoding='utf-8') as file:
    for line in file:
        line = line.strip()
        if line == '***':
            break
        data.append(line)
    # k = int(data[0])
    i = 0
    while (i < len(data)):
        k = int(data[i])
        i += 1
        if i<len(data):
            while (i<len(data) and data[i] != "*"):
                # Tạo danh sách các đối tượng trên Phố
                # Add ten dia diem
                d = data[i].split("|")
                ten_dia_diem = d[0].strip()
                # Trich xuat vi tri
                vi_tri = d[1].strip().split()
                
                vi_tri_x, vi_tri_y = changeCoor(int(vi_tri[0]), int(vi_tri[1]))
                # Trich xuat dia diem cu the
                address = d[2].strip()
                # Trich danh sach dinh ke
                data_dinh_ke = d[3].strip().split()
                t1 = int(data_dinh_ke[0])
                t2 = int(data_dinh_ke[1])
                danh_sach_dinh_ke = []
                danh_sach_dinh_ke.append(t1)
                danh_sach_dinh_ke.append(t2)

                obj = Destinations(
                    ten_dia_diem, vi_tri_x, vi_tri_y, address, danh_sach_dinh_ke, k)

                list_pho[k].danh_sach_dia_diem.append(obj)

                i += 1
        i += 1