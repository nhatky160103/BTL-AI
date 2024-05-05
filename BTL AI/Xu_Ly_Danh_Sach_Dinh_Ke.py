# Tạo ma trận đỉnh kề:
data = []
rows =24 
cols = rows
matran_dinhke = [[0] * cols for _ in range(rows)]
for i in range(rows):
    for j in range(cols):
       matran_dinhke[i][j] = -2

with open('BTL AI\Toan\Danh_Sach_Dinh_Ke.txt', 'r', encoding='utf-8') as file:
    for line in file:
        line = line.strip()
        if line == '***':
            break
        data.append(line)

    for k in range(len(data)):
        value = data[k].strip().split()
       
        i = int(value[0])
        c = value[1]
        j = int(value[2])
        k = int(value[3])
        
        if c == "=":
            matran_dinhke[i][j] = matran_dinhke[j][i] = k
        else:
            matran_dinhke[i][j] = k
