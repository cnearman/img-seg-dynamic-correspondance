'''
img.py
Created on Feb 26, 2013
@author: Chris Nearman

Image Correspondance from stereo pair.

This program takes two images which are fixed along two axes and produces an image
representation of the depth. It uses dynamic programming to calculate the disparity 
(Horizontal shift of the optimal path from the cyclopean) of each line of pixels and then outputs 
the result as a black and white image showing depth.

This program utilizes the Python Imaging Library's 'Image' module in order to read and write images.
A link to this library can be found here at 'http://www.pythonware.com/products/pil/'. 

Necessary arguments are <left_image, right_image, output_filename>.
'''

import sys
import Image

result_disparities = [] #Stores all disparities 
max_disparity = 0 #Maximum Disparity found during traceback
min_disparity = 0 #Minimum Disparity found during traceback

def main(args):
    if len(args) != 3: #Ensures proper number of arguments
        print "Invalid Arguments."
    else:
        left_image = Image.open(args[0])
        right_image = Image.open(args[1])
        output = args[2]
        if left_image.size[0] != right_image.size[0] or left_image.size[1] != right_image.size[1]:
            #Stops if the two input images are not the same size
            print "Images are incompatible sizes. Terminating."
        else:
            lpixels = list(left_image.getdata()) #All pixels from the left image
            rpixels = list(right_image.getdata()) #All pixels from the right image
            result = Image.new("RGB",(left_image.size[0],left_image.size[1])) #Result image
            for y in range(left_image.size[1]): #Iterate over all scanlines
                #Poll scanlines from both images
                lscanline = lpixels[(y * left_image.size[0]):(y * left_image.size[0]) + left_image.size[0]]
                rscanline = rpixels[(y * left_image.size[0]):(y * left_image.size[0]) + left_image.size[0]]
                #Generate array for memoization
                M = [[ -1 for i in range(len(rscanline) + 1)] for j in range(len(lscanline) + 1)]
                occlusion_cost = 40 #Cost of leaving a pixel out of of the optimal path
                generate_memos(M,rscanline,lscanline,occlusion_cost)
                disparities = [] #list of disparities from the two current scanlines
                generate_disparities(M,disparities,rscanline,lscanline,occlusion_cost)
                result_disparities.append(disparities) 
                if y % (left_image.size[1] / 10) == 0: #Displays percent completed
                    print "" + str(y / (left_image.size[1] / 10) * 10) + "% Completed"
            generate_result(result,output)

#Constructs the array of values to find the optimal correspondance between the two scanlines
def generate_memos(M, rscanline, lscanline, occlusion_cost):
    for i in range(len(rscanline) + 1): #since we know both scanlines are the same length we can do this together
                M[0][i] = i * occlusion_cost #complete vertical occlusion
                M[i][0] = i * occlusion_cost #complete horizontal occlusion
    for j in range(1,len(rscanline) + 1):
        for i in range(1,len(lscanline) + 1):
            M[j][i] = min(greyscale_difference(rscanline[j-1],lscanline[i-1]) + M[j-1][i-1],occlusion_cost + M[j-1][i], occlusion_cost + M[j][i-1])

#Uses the dynamic programming array to calculate the disparities at each row
def generate_disparities(M,disparities, rscanline, lscanline, occlusion_cost):
    i = len(M) - 1
    j = len(M) - 1
    current_disparity = 0
    while i > 1 and j > 1:
        global max_disparity
        global min_disparity
        if M[i][j] - greyscale_difference(rscanline[i-1],lscanline[j-1]) == M[i-1][j-1]:
            disparities.append(current_disparity)
            if current_disparity > max_disparity:
                max_disparity = current_disparity
            if current_disparity < min_disparity:
                min_disparity = current_disparity
            i -= 1
            j -= 1
        elif M[i][j] - occlusion_cost == M[i-1][j]:#Horizontal Occlusion
            disparities.append(current_disparity)
            if current_disparity > max_disparity:
                max_disparity = current_disparity
            if current_disparity < min_disparity:
                min_disparity = current_disparity
            current_disparity += 1
            i -= 1
        elif M[i][j] - occlusion_cost == M[i][j-1]:#Vertical Occlusion
            current_disparity -= 1
            j -= 1
        else: #Should never happen
            print "An error has occurred somewhere. Check your code"
    disparities.reverse() #reverses the list of disparities because we traceback from the end to the beginning 
    
#Constructs the resultant image from the disparities
def generate_result(result,output):
    x = 0
    y = 0
    respix = result.load()
    difference = max_disparity - min_disparity
    for scanline in result_disparities:
        for value in scanline:
            v = (value - min_disparity) * (256 / difference)
            respix[x,y] = (v,v,v)
            x +=1
        y += 1
        x = 0
    result.save(output)
    
#Calculates the difference in brightness of the two pixels
def greyscale_difference(left, right):
    lr,lb,lg = left
    rr,rb,rg = right
    la = (lr + lb + lg) / 3
    ra = (rr + rb + rg) / 3
    return abs(la - ra)

if __name__ == '__main__':
    main(sys.argv[1:])