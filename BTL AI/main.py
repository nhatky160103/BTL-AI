import PySimpleGUI as sg
from PIL import Image, ImageDraw
from DS_Street import list_pho
from DS_Street import Destinations
from Xu_Ly_Danh_Sach_Dinh_Ke import matran_dinhke
from DS_Node import danh_sach_node
from DS_Node import Node
from Astar import Astar
import copy
import time
import math


##################         Set up           ###################


# variables
sg.set_options(font=("Arial Bold", 10))
mapsize = 750
markersize = 40
rate = mapsize / float(2928)
# initial values
xP = dD = 0
buttonChooseDi = buttonChooseDen = 0
nearest = nearDi = nearDen = Destinations("Rỗng", 0, 0, "", [], 0)
chDi = chDen = (0, 0)
# direction box
directionList = []
directionLines = ""

# resize map (not recommended)

mapPath = "BTL AI\\Pics\\resized.png"
markerPath = "BTL AI\\Pics\\resized_marker.png"

img = Image.open("BTL AI\\Pics\\Map HangMa.png")
imm = img.resize((mapsize, mapsize))
imm.save(mapPath)


# combobox values
itemsPho = []  # list pho
for pho in list_pho:
    itemsPho.append(pho.ten_pho)
    
itemsDiaDiemFull = []  # list ALL destinations
dicStreet = {}  # map: pho - id pho
dicDes = {}  # map: ten+diachi - destination

# mapping
for pho in list_pho:
    dicStreet[pho.ten_pho] = pho.id
    for d in pho.danh_sach_dia_diem:
        if "Unknown" not in d.ten_dia_diem:
            line = d.ten_dia_diem + ", " + d.address
        else:
            line = d.address
        itemsDiaDiemFull.append(line)
        dicDes[line] = d
        p = (d.vi_tri_x, d.vi_tri_y)


# elements & layout
col_1 = [
        [sg.Graph(canvas_size=(mapsize, mapsize), graph_bottom_left=(0, 0),
                  graph_top_right=(mapsize, mapsize),
                  enable_events=True,  # mouse click events
                  key="-GRAPH-", pad=15)]
]

col_2 = [
        [sg.Text(text='Xuất phát', size=(8, 0)),
         sg.Combo(values=itemsPho, size=(20, 5),
                  key="-ComboPhoDi-", enable_events=True),
         sg.Combo(values=itemsDiaDiemFull, size=(40, 5), key="-ComboDiaDiemDi-", enable_events=True)],

        [sg.Text("", size=(8, 2)), sg.Button("Chọn trên bản đồ",
                                             key="-ChooseDi-", button_color=('white', 'DarkMagenta'))],

        [sg.Text(text='Điểm đến', size=(8, 0)),
         sg.Combo(values=itemsPho, size=(20, 5),
                  key="-ComboPhoDen-", enable_events=True),
         sg.Combo(values=itemsDiaDiemFull, size=(40, 5), key="-ComboDiaDiemDen-", enable_events=True)],

        [sg.Text("", size=(8, 2)), sg.Button("Chọn trên bản đồ",
                                             key="-ChooseDen-", button_color=('white', 'DarkMagenta'))],

        [sg.Button("Reset", size=(7, 0)),
         sg.Button("Tìm đường", size=(19, 0))],

        [sg.Text("Chỉ dẫn:", size=(8, 2)), sg.Multiline(
            "", size=(64, 15), key='-Direction-')]
]

layout = [
    [sg.Column(col_1), sg.Column(
        col_2, vertical_alignment="top", pad=15, justification="left")]
]

window = sg.Window('Tìm đường Hàng Mã', layout, finalize=True, margins=(0, 0))


# import map on graph
graph = window["-GRAPH-"]
image = graph.draw_image(filename=mapPath, location=(0, mapsize))


##################         Functions          ###################

# change coordinate
def changeCoor(x1, x2):
    x = round(x1*rate)
    y = mapsize - round(x2*rate)
    return x, y


# borderlines:
def d1(p):  # inside < 0
    x, y = p
    return y+0.04*x-656
def d2(p):  # inside < 0
    x, y = p
    return y+1.55*x-1297
def d3(p):      # inside > 0
    x, y = p
    return y-0.12*x-148
def d4(p):      # inside > 0
    x, y = p
    return y-5.39*x+1785
def d5(p):      # inside > 0
    x, y = p
    return y+0.02*x-28
def d6(p):  # inside < 0
    x, y = p
    return y-7.32*x+369
def d7(p):  # inside < 0
    x, y = p
    return y+0.03*x-586
def d8(p):  # inside < 0
    x, y = p
    return y-2.52*x-42


# reset everything
def reset():
    # reset variables
    global buttonChooseDi, buttonChooseDen, nearest, nearDi, nearDen, directionList, directionLines
    buttonChooseDi = buttonChooseDen = 0
    nearest = nearDi = nearDen = Destinations("init val", 0, 0, "", [], 0)
    directionLines = ""
    directionList = []

    # reset GUI
    window["-ComboPhoDi-"].update('')
    window["-ComboDiaDiemDi-"].update(values=itemsDiaDiemFull)
    window["-ComboPhoDen-"].update('')
    window["-ComboDiaDiemDen-"].update(values=itemsDiaDiemFull)
    
    window['-GRAPH-'].erase()
    graph.draw_image(
        filename=mapPath, location=(0, mapsize))

    window["-ChooseDi-"].update(button_color=('white', 'DarkMagenta'))
    window["-ChooseDen-"].update(button_color=('white', 'DarkMagenta'))
    
    window["-Direction-"].update("")


# chosen point is outside the map
def choose_again():
    sg.popup_ok("Địa điểm này nằm ngoài Hàng Mã\nHãy chọn lại",
                title="Sai địa điểm!", font=("Arial", 12))
    reset()


# check if chosen point is inside the map
def in_hang_ma(x1, x2):
    p = (x1, x2)
    if (d1(p) > 0 or d2(p) > 0 or (d3(p) < 0 and d4(p) < 0) or d5(p) < 0 or d6(p) > 0 or (d7(p) > 0 and d8(p) > 0)):
        return 0
    return 1

        
# 1 left - 2 right - 0 straight
def orientation(A, B, C):
    v1 = [B[0] - A[0], B[1] - A[1]]
    v2 = [C[0] - B[0], C[1] - B[1]]

    length1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    length2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)

    dot_product = v1[0] * v2[0] + v1[1] * v2[1]
    cos_angle = dot_product / (length1 * length2)
    angle = math.acos(cos_angle)*180/(math.pi)
    if 28 < angle < 170:
        cross_product = v1[0] * v2[1] - v1[1] * v2[0]
        if cross_product > 0:
            return 1
        elif cross_product < 0:
            return 2
    else:
        return 0
        
        
# find ten_phos of node     
def lay_duong(vv):
    ppp = vv.danh_sach_duong
    l = ""
    for i in range(len(ppp)):
       l += ppp[i].ten_pho +", "
    return l.rstrip(", ")


# draw a single line
def ve(path, dsn, mtdk,directionLines):
    i=0
    # 0 - 2
    if path[i] == 0 and path[i+1] == 2:
       directionLines= draw_0_2(directionLines)
       
    # 5 - 9
    elif mtdk[path[i]][path[i+1]] == 6:
        if dsn[path[i]].vi_tri_y > dsn[path[i+1]].vi_tri_y:
            draw_5_9(dsn[path[i]], dsn[path[i+1]])
        else:
            draw_5_9(dsn[path[i+1]], dsn[path[i]])
        
    # ngo 8 LND
    elif mtdk[path[i]][path[i+1]] == 15 and ((dsn[path[i]].ten_dinh_nut == 4 and dsn[path[i+1]].vi_tri_x == round(755*rate)) or (dsn[path[i+1]].ten_dinh_nut == 4 and dsn[path[i]].vi_tri_x == round(755*rate))):
        drawNgo8(dsn[path[i]], dsn[path[i+1]])
    
    # no car
    # pho Gam Cau, pho Hang Chai, pho Cong Duc, ngo 4 LND, ngo 12B LND, ngo 12A LND, ngo Hang Huong
    elif mtdk[path[i]][path[i+1]] == 3 or mtdk[path[i]][path[i+1]] == 8 or mtdk[path[i]][path[i+1]] == 11 or mtdk[path[i]][path[i+1]] == 14 or mtdk[path[i]][path[i+1]] == 15 or mtdk[path[i]][path[i+1]] == 16 or mtdk[path[i]][path[i+1]] == 17 or mtdk[path[i]][path[i+1]] == 18:
        des1 = (dsn[path[i]].vi_tri_x, dsn[path[i]].vi_tri_y)
        des2 = (dsn[path[i+1]].vi_tri_x, dsn[path[i+1]].vi_tri_y)
        graph.draw_line(des1, des2, color="black", width=3)
    
    # normal edges
    else:
        des1 = (dsn[path[i]].vi_tri_x, dsn[path[i]].vi_tri_y)
        des2 = (dsn[path[i+1]].vi_tri_x, dsn[path[i+1]].vi_tri_y)
        graph.draw_line(des1, des2, color="blue", width=5)

    return directionLines


# main drawing func
def draw_way(xuatPhat, dichDen):
    x1 = xuatPhat.vi_tri_x
    x2 = xuatPhat.vi_tri_y
    p1 = (x1, x2)

    x3 = dichDen.vi_tri_x
    x4 = dichDen.vi_tri_y
    p2 = (x3, x4)
    
    global directionLines,directionList
    directionLines = ""
    
    # draw start point
    # comboDi, comboDen
    if buttonChooseDi == 0 and buttonChooseDen == 0:
        graph.draw_circle(p1, 4, fill_color='blue',
                          line_color="Blue", line_width=3)
        graph.draw_circle(p1, 8, fill_color=None,
                          line_color="Blue", line_width=3)
    # comboDi, chooseDen
    if buttonChooseDi == 0 and buttonChooseDen == 1:
        graph.draw_circle(p1, 4, fill_color='blue',
                          line_color="Blue", line_width=3)
        graph.draw_circle(p1, 8, fill_color=None,
                          line_color="Blue", line_width=3)
    # chooseDi, comboDen
    if buttonChooseDi == 1 and buttonChooseDen == 0:
        draw_dotted_line(chDi, q1, 5, 5, 'blue')
        graph.draw_circle(q1, 4, fill_color='blue',
                            line_color='blue', line_width=3)
        linee = "- Đi bộ ra " + xuatPhat.address
        directionList.append(linee)
        directionLines += linee + "\n"
        window["-Direction-"].update(directionLines)
        window.refresh()
        time.sleep(1)
    # chooseDi, chooseDen
    if buttonChooseDi == 1 and buttonChooseDen == 1:
        draw_dotted_line(chDi, q1, 5, 5, 'blue')
        graph.draw_circle(q1, 4, fill_color='blue',
                            line_color='blue', line_width=3)
        linee = "--- Đi ra " +xuatPhat.address
        directionList.append(linee)
        directionLines += linee + "\n"
        window["-Direction-"].update(directionLines)
        window.refresh()
        time.sleep(1)

    # Add new nodes to matran_dinhke
    mtdk = copy.deepcopy(matran_dinhke)
    dsn = copy.deepcopy(danh_sach_node)

    desDi = Node(len(dsn), xuatPhat.vi_tri_x, xuatPhat.vi_tri_y, [])
    desDen = Node(len(dsn)+1, dichDen.vi_tri_x, dichDen.vi_tri_y, [])

    dsn.append(desDi)
    dsn.append(desDen)

    a = dsn.index(desDi)
    b = dsn.index(desDen)
    x = xuatPhat.danh_sach_dinh_ke[0]
    y = xuatPhat.danh_sach_dinh_ke[1]
    z = dichDen.danh_sach_dinh_ke[0]
    t = dichDen.danh_sach_dinh_ke[1]

    if y == -1:
        mtdk[x][a] = mtdk[a][x] = xuatPhat.thuoc_pho
    else:
        if mtdk[y][x] != -2:
            mtdk[x][a] = mtdk[a][x] = mtdk[y][a] = mtdk[a][y] = mtdk[y][x]
            
        else:
            mtdk[x][a] = mtdk[a][y] = mtdk[x][y]
            

    if t == -1:
        mtdk[z][b] = mtdk[b][z] = dichDen.thuoc_pho
    else:
        if mtdk[t][z] != -2:
            mtdk[z][b] = mtdk[b][z] = mtdk[t][b] = mtdk[b][t] = mtdk[t][z]
           
        else:
            mtdk[z][b] = mtdk[b][t] = mtdk[z][t]

    if x == z and y == t:
        if y == -1:
            if dist(desDi.vi_tri_x, desDi.vi_tri_y, dsn[x].vi_tri_x, dsn[x].vi_tri_y) < dist(desDen.vi_tri_x, desDen.vi_tri_y, dsn[x].vi_tri_x, dsn[x].vi_tri_y):
                    
                mtdk[x][b] = mtdk[b][x] = -2
                mtdk[a][b] = mtdk[b][a] = dichDen.thuoc_pho
            else:
                mtdk[x][a] = mtdk[a][x] = -2
                mtdk[a][b] = mtdk[b][a] = dichDen.thuoc_pho
        else:
            if(mtdk[y][x]==-2):
                if dist(desDi.vi_tri_x, desDi.vi_tri_y, dsn[x].vi_tri_x, dsn[x].vi_tri_y) < dist(desDen.vi_tri_x, desDen.vi_tri_y, dsn[x].vi_tri_x, dsn[x].vi_tri_y):
                    mtdk[x][b] = mtdk[a][y] = -2
                    mtdk[x][a] = mtdk[a][b] = mtdk[b][y] = mtdk[x][y]
                else:
                    mtdk[x][a] = mtdk[b][y] = -2
                    mtdk[x][b] = mtdk[b][a] = mtdk[a][y] = mtdk[x][y]
            else:
                if dist(desDi.vi_tri_x, desDi.vi_tri_y, dsn[x].vi_tri_x, dsn[x].vi_tri_y) < dist(desDen.vi_tri_x, desDen.vi_tri_y, dsn[x].vi_tri_x, dsn[x].vi_tri_y):
                    mtdk[x][b] = mtdk[a][y] = mtdk[b][x]=mtdk[y][a] = -2
                    mtdk[b][a] = mtdk[a][b]  = mtdk[x][y]
                else:
                    mtdk[x][a] = mtdk[b][y] = mtdk[a][x]= mtdk[y][b] =  -2
                    mtdk[b][a] = mtdk[a][b]  = mtdk[x][y]
    if(y != -1) :
        mtdk[x][y] = mtdk[y][x] = -2
    if(t!=-1):
        mtdk[z][t] = mtdk[t][z] = -2

    # apply A*
    path = Astar(mtdk, dsn, 22, 23)

    # 0 2: duong ngang pho Quan Thanh
    p= []
    chihuong = []
    for i in range(len(path)-2):
        cur = (dsn[path[i]].vi_tri_x, dsn[path[i]].vi_tri_y)  # current node
        nex = (dsn[path[i+1]].vi_tri_x, dsn[path[i+1]].vi_tri_y) # next node
        nexx = (dsn[path[i+2]].vi_tri_x, dsn[path[i+2]].vi_tri_y) # next next node
        ori = orientation(cur, nex, nexx)
        
        if(path[i+1]==0 and path[i+2]==2): ori = 3
        if(path[i]==0 and path[i+1]==2): ori = 4
        p.append((path[i],path[i+1],ori))
        
    p.append((path[len(path)-2],path[-1],-1))
  
    # draw lines, show direction
    i = 0
    li=directionLines
    while i<len(p)-1:
        if(p[i][0]!=0 or p[i][1]!=2):
            li += "- Đi thẳng "+ list_pho[mtdk[p[i][0]][p[i][1]]].ten_pho +" đến "
            whitep = (dsn[p[i][0]].vi_tri_x, dsn[p[i][0]].vi_tri_y)
            graph.draw_circle(whitep, 4, fill_color='blue',
                                          line_color='blue', line_width=3)
            while(p[i][2]==0 and mtdk[p[i][0]][p[i][1]] == mtdk[p[i+1][0]][p[i+1][1]] ):
                ve((p[i][0],p[i][1]),dsn,mtdk,li)
                i +=1
            if i<len(p)-1:
                if(p[i][2]==3):
                    ve((p[i][0],p[i][1]),dsn,mtdk,li)
                    li += "ngã rẽ "+ lay_duong(dsn[0])+", Phố Hàng Đậu \n"
                    window["-Direction-"].update(li)
                    # Neu di tu Hang Cot len
                    if mtdk[p[i][0]][p[i][1]]==2:
                        li += "- Rẽ phải vào phố Hàng Đậu\n"
                        window["-Direction-"].update(li)
                        
                        whitep = (dsn[p[i][1]].vi_tri_x, dsn[p[i][1]].vi_tri_y)
                        graph.draw_circle(whitep, 4, fill_color='blue',
                                          line_color='blue', line_width=3)
                        
                        window.refresh()
                        time.sleep(1)
                        
                        li += "- Đi thẳng phố Hàng Đậu đến ngã rẽ phố Hàng Than phố Hàng Đậu\n"
                        li = ve((p[i+1][0],p[i+1][1]), dsn, mtdk, li)
                        
                        if(mtdk[p[i+2][0]][p[i+2][1]]==1):
                            li += "- Đi thẳng phố Phan Đình Phùng đến ngã rẽ phố Lý Nam Đế phố Phan Đình Phùng\n" 
                            li += "- Rẽ phải vào phố Lý Nam Đế \n"
                            window["-Direction-"].update(li)
       
                            whitep = (dsn[p[i+2][0]].vi_tri_x,
                                      dsn[p[i+2][0]].vi_tri_y)
                            graph.draw_circle(whitep, 4, fill_color='blue',
                                              line_color='blue', line_width=3)
                            
                            window.refresh()
                            time.sleep(1)
                            
                    else:
                        window.refresh()
                        time.sleep(1)
                        li +="- Đi thẳng vào phố Hằng Đậu đến ngã rẽ phố Hàng Than phố Hàng Đậu\n"
                        window["-Direction-"].update(li)
                        li = ve((p[i+1][0],p[i+1][1]),dsn,mtdk,li)
                        if(mtdk[p[i+2][0]][p[i+2][1]]==1): 
                            li += "- Đi thẳng phố Phan Đình Phùng đến ngã rẽ phố Lý Nam Đế phố Phan Đình Phùng\n" 
                            li += "- Rẽ phải vào phố Lý Nam Đế \n"
                            window["-Direction-"].update(li)

                            whitep = (dsn[p[i+2][0]].vi_tri_x,
                                      dsn[p[i+2][0]].vi_tri_y)
                            graph.draw_circle(whitep, 4, fill_color='blue',
                                              line_color='blue', line_width=3)
                            
                            window.refresh()
                            time.sleep(1)

                elif(p[i][2]!=0):
                    ve((p[i][0],p[i][1]),dsn,mtdk,li)
                    li += "ngã rẽ "+ lay_duong(dsn[p[i][1]])+"\n"
                    if(p[i][2]==1):
                        li += "- Rẽ trái vào " +list_pho[mtdk[p[i+1][0]][p[i+1][1]]].ten_pho +  "\n"
                    else: 
                        li += "- Rẽ phải vào " +list_pho[mtdk[p[i+1][0]][p[i+1][1]]].ten_pho +  "\n"
                    window["-Direction-"].update(li)
                    
                    whitep = (dsn[p[i+1][0]].vi_tri_x, dsn[p[i+1][0]].vi_tri_y)
                    graph.draw_circle(whitep, 4, fill_color='blue', line_color='blue', line_width=3)
                    
                    window.refresh()
                    time.sleep(1)
                            
                else:
                    ve((p[i][0],p[i][1]),dsn,mtdk,li)
                    li += "ngã rẽ "+ lay_duong(dsn[p[i][1]])+"\n"
                    li += "- Đi thẳng vào " +list_pho[mtdk[p[i+1][0]][p[i+1][1]]].ten_pho +  "\n"
                    window["-Direction-"].update(li)
                    
                    whitep = (dsn[p[i+1][0]].vi_tri_x, dsn[p[i+1][0]].vi_tri_y)
                    graph.draw_circle(whitep, 4, fill_color='blue', line_color='blue', line_width=3)
             
                    window.refresh()
                    time.sleep(1)
                            

        i +=1
    
    # last one
    i= len(p)-1
    ve((p[i][0],p[i][1]), dsn, mtdk, directionLines)
    if(p[i-1][2]!=0 or mtdk[p[i][0]][p[i][1]] != mtdk[p[i-1][0]][p[i-1][1]]): li += "- Đi thẳng " + list_pho[mtdk[p[i][0]][p[i][1]]].ten_pho +" đến "
    li +=  dichDen.address
    window["-Direction-"].update(li)
    whitep = (dichDen.vi_tri_x, dichDen.vi_tri_y)
    graph.draw_circle(whitep, 4, fill_color='blue',
                      line_color='blue', line_width=3)
    window.refresh()
    time.sleep(1)
    directionLines = li+"\n"

    # draw end point
    # comboDi, comboDen
    if buttonChooseDi == 0 and buttonChooseDen == 0:
        graph.draw_circle(q2, 4, fill_color='blue',
                          line_color='blue', line_width=3)
        graph.draw_image(filename=markerPath,
                         location=(p2[0]-19, p2[1]+37))
        linee = "--- ĐÃ ĐẾN!!!"
        directionList.append(linee)
        directionLines += linee + "\n"
        window["-Direction-"].update(directionLines)
    # comboDi, chooseDen
    if buttonChooseDi == 0 and buttonChooseDen == 1:
        draw_dotted_line(chDen, q2, 5, 5, 'blue')
        graph.draw_circle(q2, 3, fill_color='blue',
                            line_color='blue', line_width=3)
        graph.draw_image(filename=markerPath,
                            location=(chDen[0]-19, chDen[1]+37))
        linee = "--- Đi vào là đến!!!"
        directionList.append(linee)
        directionLines += linee + "\n"
        window["-Direction-"].update(directionLines)    
    # chooseDi, comboDen
    if buttonChooseDi == 1 and buttonChooseDen == 0:
        graph.draw_circle(q2, 4, fill_color='blue',
                          line_color='blue', line_width=3)
        graph.draw_image(filename=markerPath,
                         location=(p2[0]-19, p2[1]+37))
        linee = "--- ĐÃ ĐẾN!!!"
        directionList.append(linee)
        directionLines += linee + "\n"
        window["-Direction-"].update(directionLines)
    # chooseDi, chooseDen
    if buttonChooseDi == buttonChooseDen == 1:
        draw_dotted_line(chDen, q2, 5, 5, 'blue')
        graph.draw_circle(q2, 4, fill_color='blue',
                          line_color='blue', line_width=3)
        graph.draw_image(filename=markerPath,
                            location=(chDen[0]-19, chDen[1]+37))
        linee = "--- Đi vào là đến!!!"
        directionList.append(linee)
        directionLines += linee + "\n"
        window["-Direction-"].update(directionLines)
        
        
# draw curved path        
def draw_0_2(directionLines):
    graph.draw_line((1670*rate, mapsize - 425*rate),
                    (1930*rate, mapsize - 355*rate), color="blue", width=5)
    directionLines +="- Rẽ trái vào phố Hàng Than\n"
    window["-Direction-"].update(directionLines)
    
    whitep = (1930*rate, mapsize - 355*rate)
    graph.draw_circle(whitep, 4, fill_color='blue',
                      line_color='blue', line_width=3)
    
    window.refresh()
    time.sleep(1)
    
    graph.draw_line((1930*rate, mapsize - 355*rate),
                    (1880*rate, mapsize - 210*rate), color="blue", width=5)
    directionLines += "- Đi thẳng phố Hàng Than đến ngã rẽ phố Quán Thánh phố Hàng Than\n" +"- Rẽ trái vào phố Quán Thánh\n"
    window["-Direction-"].update(directionLines)
    
    whitep = (1880*rate, mapsize - 210*rate)
    graph.draw_circle(whitep, 4, fill_color='blue',
                      line_color='blue', line_width=3)
    
    window.refresh()
    time.sleep(1)
    
    graph.draw_line((1880*rate, mapsize - 210*rate),
                    (1677*rate, mapsize - 216*rate), color="blue", width=5)
    graph.draw_line((1677*rate, mapsize - 216*rate), (915*rate,
                    mapsize - 125*rate), color="blue", width=5)
    directionLines +="- Đi thẳng phố Quán Thánh đến ngã rẽ phố Hòe Nhai phố Quán Thánh\n" +"- Rẽ trái vào phố Hòe Nhai\n"
    window["-Direction-"].update(directionLines)

    whitep = (915*rate, mapsize - 125*rate)
    graph.draw_circle(whitep, 4, fill_color='blue',
                      line_color='blue', line_width=3)

    window.refresh()
    time.sleep(1)
    
    graph.draw_line((915*rate, mapsize - 125*rate), (845*rate,
                    mapsize - 345*rate), color="blue", width=5)
    directionLines +="- Đi thẳng phố Hòe Nhai đến ngã rẽ phố Phan Đình Phùng phố Hòe Nhai\n" +"- Rẽ trái vào phố Phan Đình Phùng\n"
    window["-Direction-"].update(directionLines)
    
    whitep = (845*rate, mapsize - 345*rate)
    graph.draw_circle(whitep, 4, fill_color='blue',
                      line_color='blue', line_width=3)
    
    window.refresh()
    time.sleep(1)
    
    graph.draw_line((845*rate, mapsize - 345*rate), (1110*rate,
                    mapsize - 400*rate), color="blue", width=5)
    
    return directionLines


# no car
def drawNgo8(X1, X2):
    p = changeCoor(890, 921)
    graph.draw_line((X1.vi_tri_x, X1.vi_tri_y), p, color="black", width=3)
    graph.draw_line(p, (X2.vi_tri_x, X2.vi_tri_y), color="black", width=3)


def draw_5_9(X1, X2): # y-coordinate decreasing
    data59 = []  
    coor5 = changeCoor(1660, 1010)
    with open('BTL AI\\Toan\\NamChin.txt', 'r', encoding='utf-8') as file:
        data59.append(coor5)
        for line in file:
            line = line.strip()
            if line == '***':
                break
            l = line.split()
            x1, x2 = l[0], l[1]
            x1 = int(x1)
            x2 = int(x2)
            pi = changeCoor(x1, x2)
            data59.append(pi)

    if X1.ten_dinh_nut == 5 and X2.ten_dinh_nut == 9:
        for i in range(len(data59)-1):
            graph.draw_line(data59[i], data59[i+1], color='blue', width=5)
    elif X1.ten_dinh_nut == 5:
        i = len(data59) - 1
        while (data59[i][1] < X2.vi_tri_y):
            i -= 1
        for j in range(i):
            graph.draw_line(data59[j], data59[j+1], color='blue', width=5)
        graph.draw_line(
            data59[i], (X2.vi_tri_x, X2.vi_tri_y), color='blue', width=5)
    elif X2.ten_dinh_nut == 9:
        i = 0
        while (data59[i][1] > X1.vi_tri_y):
            i += 1
        graph.draw_line((X1.vi_tri_x, X1.vi_tri_y),
                        data59[i], color='blue', width=5)
        for j in range(i, len(data59)-1):
            graph.draw_line(data59[j], data59[j+1], color='blue', width=5)
    else:
        i = 0
        while (data59[i][1] > X1.vi_tri_y):
            i += 1
        j = len(data59) - 1
        while (data59[j][1] < X2.vi_tri_y):
            j -= 1

        graph.draw_line((X1.vi_tri_x, X1.vi_tri_y),
                        data59[i], color='blue', width=5)
        for k in range(i, j):
            graph.draw_line(data59[k], data59[k+1], color='blue', width=5)
        graph.draw_line(
            data59[j], (X2.vi_tri_x, X2.vi_tri_y), color='blue', width=5)


# draw dotted line
def draw_dotted_line(start_point, end_point, dot_size=1, gap_size=1, color='blue'):
    dx = end_point[0] - start_point[0]
    dy = end_point[1] - start_point[1]
    distance = max(abs(dx), abs(dy))
    if distance == 0:
        return

    step_x = dx / distance / 2
    step_y = dy / distance / 2

    for i in range(0, distance*2, dot_size + gap_size):
        x = int(start_point[0] + i * step_x)
        y = int(start_point[1] + i * step_y)
        x_end = int(x + dot_size * step_x)
        y_end = int(y + dot_size * step_y)
        graph.draw_line((x, y), (x_end, y_end), color=color, width=3)


# distance^2 between 2 coordinates (x1, x2) & (x3, x4)
def dist(x1, x2, x3, x4):
    return (x1-x3)**2+(x2-x4)**2


# return the nearest destination
def nearestDes(x1, x2):
    minn = round((mapsize*1.414)**2)  # length of the diagonal
    for pho in list_pho:
        for des in pho.danh_sach_dia_diem:
            x3 = des.vi_tri_x
            x4 = des.vi_tri_y
            distt = dist(x1, x2, x3, x4)
            if distt < minn:
                minn = distt
                nearest = des
    return nearest


##################         Event handler          ###################


while True:
    event, values = window.read()
    # print(event, values)
    match event:
        case sg.WINDOW_CLOSED:
            break

        # mutually dependent comboboxes: Pho -> Des
        case "-ComboPhoDi-":
            buttonChooseDi = 0
            index = dicStreet[values["-ComboPhoDi-"]]
            listDes = []
            for d in list_pho[index].danh_sach_dia_diem:
                if "Unknown" not in d.ten_dia_diem:
                    line = d.ten_dia_diem + ", " + d.address
                else:
                    line = d.address
                listDes.append(line)
            window["-ComboDiaDiemDi-"].update(values=listDes)
            
        case "-ComboPhoDen-":
            buttonChooseDen = 0
            index = dicStreet[values["-ComboPhoDen-"]]
            listDes = []
            for d in list_pho[index].danh_sach_dia_diem:
                if "Unknown" not in d.ten_dia_diem:
                    line = d.ten_dia_diem + ", " + d.address
                else:
                    line = d.address
                listDes.append(line)
            window["-ComboDiaDiemDen-"].update(values=listDes)
            
        case "-ComboDiaDiemDi-":
            if xP == 1:
                if dD == 1:
                    if values["-ComboDiaDiemDen-"] != '':
                        graph.draw_image(filename=mapPath, location=(0, mapsize))
                        dichDen = dicDes[values["-ComboDiaDiemDen-"]]
                        tmp = (dichDen.vi_tri_x, dichDen.vi_tri_y)
                        graph.draw_circle(tmp, 4, fill_color='blue',
                                    line_color='blue', line_width=3)
                        graph.draw_image(filename=markerPath,
                                        location=(tmp[0]-19, tmp[1]+37))
                    elif buttonChooseDen == 1:
                        graph.draw_image(filename=mapPath,
                                         location=(0, mapsize))
                        graph.draw_circle(
                        chDen, 4, fill_color='blue', line_color="Blue", line_width=3)
                        graph.draw_image(filename=markerPath, location=(
                        chDen[0]-19, chDen[1]+37))
                else:
                    graph.draw_image(filename=mapPath, location=(0, mapsize))
            
            if (values["-ComboDiaDiemDi-"] != ''):
                xP = 1
            
            buttonChooseDi = 0
            
            xuatPhat = dicDes[values["-ComboDiaDiemDi-"]]
            tmp = (xuatPhat.vi_tri_x, xuatPhat.vi_tri_y)
            graph.draw_circle(tmp, 4, fill_color='blue',
                        line_color="Blue", line_width=3)
            graph.draw_circle(tmp, 8, fill_color=None,
                        line_color="Blue", line_width=3)
            
            window["-Direction-"].update("")
            
        case "-ComboDiaDiemDen-":
            
            if dD == 1:
                if xP == 1:
                    if values["-ComboDiaDiemDi-"] != '':
                        graph.draw_image(filename=mapPath, location=(0, mapsize))
                        xuatPhat = dicDes[values["-ComboDiaDiemDi-"]]
                        tmp = (xuatPhat.vi_tri_x, xuatPhat.vi_tri_y)
                        graph.draw_circle(tmp, 4, fill_color='blue',
                                    line_color="Blue", line_width=3)
                        graph.draw_circle(tmp, 8, fill_color=None,
                                    line_color="Blue", line_width=3)
                    elif buttonChooseDi == 1:
                        graph.draw_image(filename=mapPath, location=(0, mapsize))
                        graph.draw_circle(
                        chDi, 4, fill_color='blue', line_color="Blue", line_width=3)
                        graph.draw_circle(
                        chDi, 8, fill_color=None, line_color="Blue", line_width=3)
                else:
                    graph.draw_image(filename=mapPath, location=(0, mapsize))
            
            if (values["-ComboDiaDiemDen-"] != ''):
                dD = 1
            
            buttonChooseDen = 0
            
            dichDen = dicDes[values["-ComboDiaDiemDen-"]]
            tmp = (dichDen.vi_tri_x, dichDen.vi_tri_y)
            graph.draw_circle(tmp, 4, fill_color='blue',
                        line_color='blue', line_width=3)
            graph.draw_image(filename=markerPath,
                            location=(tmp[0]-19, tmp[1]+37))
            
            window["-Direction-"].update("")


        # Choose on map -> nearDi, nearDen
        case "-ChooseDi-":
            if xP == 1:
                if dD == 1:
                    if values["-ComboDiaDiemDen-"] != '':
                        graph.draw_image(filename=mapPath, location=(0, mapsize))
                        dichDen = dicDes[values["-ComboDiaDiemDen-"]]
                        tmp = (dichDen.vi_tri_x, dichDen.vi_tri_y)
                        graph.draw_circle(tmp, 4, fill_color='blue',
                                    line_color='blue', line_width=3)
                        graph.draw_image(filename=markerPath,
                                        location=(tmp[0]-19, tmp[1]+37))
                    elif buttonChooseDen == 1:
                        graph.draw_image(filename=mapPath,
                                         location=(0, mapsize))
                        graph.draw_circle(
                        chDen, 4, fill_color='blue', line_color="Blue", line_width=3)
                        graph.draw_image(filename=markerPath, location=(
                        chDen[0]-19, chDen[1]+37))
                else:
                    graph.draw_image(filename=mapPath, location=(0, mapsize))
            
            buttonChooseDi = 1
            delMap = 0
            window["-ChooseDi-"].update(button_color=('white', 'orange'))
            
            window["-ComboPhoDi-"].update('')
            window["-ComboDiaDiemDi-"].update('')
            window["-Direction-"].update("")
            
            # get coordinate
            event, values = window.read()
            window["-ChooseDi-"].update(button_color=('white', 'DarkMagenta'))
            if event == "-GRAPH-":
                chDi = values["-GRAPH-"]
                
                if chDi:
                    xP = 1
                
                x1, x2 = chDi[0], chDi[1]

                if in_hang_ma(x1, x2):
                    # draw start point
                    graph.draw_circle(
                        chDi, 4, fill_color='blue', line_color="Blue", line_width=3)
                    graph.draw_circle(
                        chDi, 8, fill_color=None, line_color="Blue", line_width=3)
                    # Des: nearDi
                    nearDi = nearestDes(x1, x2)

                else:
                    choose_again()
            else:
                buttonChooseDi = 0

        case "-ChooseDen-":
            
            if dD == 1:
                if xP == 1:
                    if values["-ComboDiaDiemDi-"] != '':
                        graph.draw_image(filename=mapPath,
                                         location=(0, mapsize))
                        xuatPhat = dicDes[values["-ComboDiaDiemDi-"]]
                        tmp = (xuatPhat.vi_tri_x, xuatPhat.vi_tri_y)
                        graph.draw_circle(tmp, 4, fill_color='blue',
                                          line_color="Blue", line_width=3)
                        graph.draw_circle(tmp, 8, fill_color=None,
                                          line_color="Blue", line_width=3)
                    elif buttonChooseDi == 1:
                        graph.draw_image(filename=mapPath,
                                         location=(0, mapsize))
                        graph.draw_circle(
                            chDi, 4, fill_color='blue', line_color="Blue", line_width=3)
                        graph.draw_circle(
                            chDi, 8, fill_color=None, line_color="Blue", line_width=3)
                else:
                    graph.draw_image(filename=mapPath, location=(0, mapsize))
            
            buttonChooseDen = 1
            delMap = 0
            window["-ChooseDen-"].update(button_color=('white', 'orange'))

            window["-ComboPhoDen-"].update('')
            window["-ComboDiaDiemDen-"].update('')
            window["-Direction-"].update("")
            
            # get coordinate
            event, values = window.read()
            window["-ChooseDen-"].update(button_color=('white', 'DarkMagenta'))
            if event == "-GRAPH-":
                chDen = values["-GRAPH-"]
                
                if chDen:
                    dD = 1
                
                x1, x2 = chDen[0], chDen[1]

                if in_hang_ma(x1, x2):
                    # draw end point
                    graph.draw_circle(
                        chDen, 4, fill_color='blue', line_color="Blue", line_width=3)
                    graph.draw_image(filename=markerPath, location=(
                        chDen[0]-19, chDen[1]+37))

                    # Des: nearDen
                    nearDen = nearestDes(x1, x2)

                else:
                    choose_again()
            else:
                buttonChooseDen = 0

        case "Tìm đường":
            # No start/end point
            if values["-ComboDiaDiemDi-"] == '' and buttonChooseDi == 0:
                sg.popup_ok("Hãy chọn điểm xuất phát!",
                            title="Chưa chọn địa điểm!", font=("Arial", 12))
                continue
            if values["-ComboDiaDiemDen-"] == '' and buttonChooseDen == 0:
                sg.popup_ok("Hãy chọn đích đến!",
                            title="Chưa chọn địa điểm!", font=("Arial", 12))
                continue

            # comboDi, comboDen
            if values["-ComboDiaDiemDi-"] != '' and values["-ComboDiaDiemDen-"] != '':
                xuatPhat = dicDes[values["-ComboDiaDiemDi-"]]
                dichDen = dicDes[values["-ComboDiaDiemDen-"]]

                q1 = (xuatPhat.vi_tri_x, xuatPhat.vi_tri_y)
                q2 = (dichDen.vi_tri_x, dichDen.vi_tri_y)

                if q1 == q2:
                    graph.draw_circle(q1, 4, fill_color='blue',
                                    line_color="Blue", line_width=3)
                    graph.draw_circle(q1, 8, fill_color=None,
                                    line_color="Blue", line_width=3)
                    window["-Direction-"].update("ĐÃ ĐẾN!")
                else:
                    draw_way(xuatPhat, dichDen)
            # chooseDi, chooseDen
            elif buttonChooseDi == 1 and buttonChooseDen == 1:
                q1 = (nearDi.vi_tri_x, nearDi.vi_tri_y)
                q2 = (nearDen.vi_tri_x, nearDen.vi_tri_y)
                if q1 == q2:
                    window["-Direction-"].update("Đi bộ là đến!")
                    draw_dotted_line(
                        chDi, chDen, 5, 5, 'blue')
                else:
                    draw_way(nearDi, nearDen)
                    
            # comboDi, chooseDen
            elif values["-ComboDiaDiemDi-"] != '' and buttonChooseDen == 1:
                xuatPhat = dicDes[values["-ComboDiaDiemDi-"]]
                q1 = (xuatPhat.vi_tri_x, xuatPhat.vi_tri_y)
                q2 = (nearDen.vi_tri_x, nearDen.vi_tri_y)
                if q1 == q2:
                    window["-Direction-"].update("Đi bộ là đến!")
                    draw_dotted_line(
                        q1, chDen, 5, 5, 'blue')
                else:
                    draw_way(xuatPhat, nearDen)
                    
            # chooseDi, comboDen
            elif buttonChooseDi == 1 and values["-ComboDiaDiemDen-"] != '':
                dichDen = dicDes[values["-ComboDiaDiemDen-"]]
                q1 = (nearDi.vi_tri_x, nearDi.vi_tri_y)
                q2 = (dichDen.vi_tri_x, dichDen.vi_tri_y)
                if q1 == q2:
                    window["-Direction-"].update("Đi bộ là đến!")
                    draw_dotted_line(
                        chDi, q2, 5, 5, 'blue')
                else:
                    draw_way(nearDi, dichDen)
            
        case "Reset":
            reset()

window.close()
