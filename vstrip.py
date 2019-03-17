import cv2
import numpy as np
import pickle

#100 is width of strip
s_width = 100
s_cnt = 5
#min gap between two lines
space_thres  = 10
#max no of pixel vals in a line to qualify as empty line
count_thres = 5

def preprocessImage(image):
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    cv2.fastNlMeansDenoising(gray,gray)
    #binary
    ret,image = cv2.threshold(gray,128,255,cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    return image



def calcThresholds(strips):
    mid=len(strips)//2
    (rows1,cols1)=strips[mid].shape
    strip_mid=strips[mid]
    #print(strip_mid)
    tot_count_w = 0
    count_whitepx=[]
    for i in range(1,rows1-1):
        count_w = 0
        for j in range(cols1):
            vals = strip_mid[i][j]
            if(vals == 255): #Look for white pixels
                count_w = count_w +1
        tot_count_w+=count_w
        count_whitepx.append(count_w)
    #max no of pixel vals in a line to qualify as empty line
    count_thres=tot_count_w//rows1
    #200 is width of strip
    s_width = 100
    seen=False
    min_space=0
    min_spaces=[]
    first_line=True
    word_ht=0
    sum_word_ht=0
    word_hts=[]
    no_words=0
    for i in range(1,rows1-1):
        if(count_whitepx[i-1]<=count_thres):
            if(not seen):
                seen=True
                min_space=0
            else:
                min_space+=1
            if not first_line and word_ht>10:
                #print("word ht",word_ht)
                sum_word_ht+=word_ht
                word_hts.append(word_ht)
                word_ht=0
                no_words+=1
                first_line=True
        else:
            if(min_space!=0):
                min_spaces.append(min_space)
                min_space=0
                seen=False
            if first_line:
                first_line=False
            word_ht+=1
    min_spaces.sort()
    space_thres=min_spaces[round(0.5*len(min_spaces))]//2
    avg_word_ht=sum_word_ht//no_words
    word_hts.sort()
    avg_word_ht=word_hts[round(0.25*len(word_hts))]
    s_cnt = count_thres
    #min gap between two lines
    #space_thres  = 10
    return s_width,space_thres,count_thres,avg_word_ht

def obtainStrips(image):
    (rows,cols)=image.shape
    strips=[]
    for i in range(0,cols,s_width):
        if(i+s_width<cols): #Not end of the image
            strips.append(image[0:rows,i:i+s_width])
        else: #For the end of the image
            strips.append(image[0:rows,i:cols])
    return strips



def segmentStrips(strips):
    gaps_arr = []
    count_arr = [] #Array of count_strips

    for simg in strips:
        (rows1,cols1)=simg.shape
        x=[]
        count_strip = [] # Count the white px for each row of a strip
        seen=False
        for i in range(1,rows1-1):
            count_w = 0
            nxt_cnt_w = 0
            prev_cnt_w= 0
            for j in range(cols1):
                vals = simg[i][j]
                nxt_vals = simg[i+1][j]
                prev_vals = simg[i-1][j]
                if(vals == 255): #Look for white pixels
                    count_w = count_w +1
                if(nxt_vals == 255):
                    nxt_cnt_w = nxt_cnt_w +1 
                if(prev_vals ==255): #Look for white pixels
                    prev_cnt_w = prev_cnt_w +1
            #print(count_w)
            count_strip.append(count_w)
            if count_w<=s_cnt and (nxt_cnt_w>s_cnt or prev_cnt_w >s_cnt):
                '''if(len(x)!=0):
                    if(x[len(x)-1]==i-1):
                        x.pop()'''
                if(not seen):
                    x.append(i)
                    seen=True
            else:
                seen=False
        count_arr.append(count_strip)
        gaps_arr.append(x)
    

    mid_arr = []
    #gaps_arr and mid_arr are array of arrays 
    #gaps_arr has the gap of each strip - gaps of each strip is an array
 
    for gfs in gaps_arr:
        y=[]
        for gap_i in range(0,len(gfs)-1):
            space_diff = gfs[gap_i+1] - gfs[gap_i]
            if(gap_i!=0 and len(y)!=0):
                gap_diff=gfs[gap_i]-y[len(y)-1]+space_diff//2
                if(gap_diff<avg_word_ht):
                    continue
                elif(space_diff>space_thres):
                    mid_pt = gfs[gap_i] + space_diff//2
                    y.append(mid_pt)
            if(space_diff>space_thres):
                mid_pt = gfs[gap_i] + space_diff//2
                y.append(mid_pt)
        mid_arr.append(y)

    #print(gaps_arr[1])
    #print(mid_arr[1])

    final_px = []
    # j is indiv strip no
    

    for j in range(len(mid_arr)):
        z = []
        for i in range(len(mid_arr[j])):
            if(count_arr[j][mid_arr[j][i]]<=count_thres):
                z.append(mid_arr[j][i])
                cv2.line(image,(s_width*j,mid_arr[j][i]),(s_width*(j+1),mid_arr[j][i]),(255,0,0),thickness=1)
        if(len(z)!=0):
            final_px.append(z)

    return image , final_px , mid_arr


def combineStrips(final_px , mid_arr):
    strips_no = len(mid_arr)
    no_of_lines=min([len(x) for x in final_px])
    #no_of_lines=len(final_px[0])
    final_lines = []
    n_img =[ ]
    print(no_of_lines)
    (rows,cols)=image.shape
    j=0
    #for i in range(0,mid_arr[j][0]):
    #print(final_px[0][0])
    prev_final_px=0

    for n_line in range(0,no_of_lines-1):
        s=0
        n_img=[]
        for j in range(1, strips_no-1):
            if(s+s_width<cols):
                temp_img = image[prev_final_px:final_px[j][n_line] , s:s+s_width]
                s = s+s_width
            else:
                temp_img = image[prev_final_px:final_px[j][n_line] , s:cols ]
        
            if(n_img==[]):
                n_img=temp_img
            else:
                temp=[]
                for i in range(prev_final_px,final_px[j][n_line]):
                    if(i<len(n_img) and i<len(temp_img)):
                        temp.append(np.concatenate((n_img[i] , temp_img[i])))
                    else:
                        break
                n_img=np.array(temp)
            prev_final_px=final_px[j][n_line]

        nnn_img = np.array(n_img)
        cv2.imwrite('op/fl.jpg' ,nnn_img)

images=[2,3,4,5,6,7,8,9,10]
for im_no in images:
    if(im_no==3):
        image = cv2.imread('images/'+str(im_no)+'.jpg')
        im = cv2.imread('images/'+str(im_no)+'.jpg')
        image = preprocessImage(image)
        '''strips = obtainStrips(image)
        pickle_out = open(str(im_no)+".pickle","wb")
        pickle.dump(strips, pickle_out)
        pickle_out.close()
        '''
        pickle_in = open(str(im_no)+".pickle","rb")
        strips = pickle.load(pickle_in)
        s_width,space_thres,count_thres,avg_word_ht=calcThresholds(strips)
        print(space_thres)
        image , final_px , mid_arr = segmentStrips(strips)
        cv2.imwrite('op/'+str(im_no)+"_thr1.jpg",image)

