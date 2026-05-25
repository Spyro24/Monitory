def get_color_safe(idx, offset_idx, alpha_color):
    try:
        color = distinct_colors[int(idx + offset_idx) % 64]
    except:
        try:
            color = distinct_colors[int(idx) % 64]
        except:
            color = distinct_colors[0]
    return (color[0], color[1], color[2], alpha_color)


distinct_colors = [ # Set of 64 colors
(47, 79, 79), # darkslategray
(85, 107, 47), # darkolivegreen
(107, 142, 35), # olivedrab
(160, 82, 45), # sienna
(46, 139, 87), # seagreen
(127, 0, 0), # maroon2
(25, 25, 112), # midnightblue
(112, 128, 144), # slategray
(72, 61, 139), # darkslateblue
(95, 158, 160), # cadetblue
(0, 128, 0), # green
(188, 143, 143), # rosybrown
(102, 51, 153), # rebeccapurple
(184, 134, 11), # darkgoldenrod
(189, 183, 107), # darkkhaki
(205, 133, 63), # peru
(70, 130, 180), # steelblue
(210, 105, 30), # chocolate
(154, 205, 50), # yellowgreen
(32, 178, 170), # lightseagreen
(0, 0, 139), # darkblue
(50, 205, 50), # limegreen
(143, 188, 143), # darkseagreen
(139, 0, 139), # darkmagenta
(176, 48, 96), # maroon3
(102, 205, 170), # mediumaquamarine
(153, 50, 204), # darkorchid
(255, 0, 0), # red
(255, 165, 0), # orange
(255, 215, 0), # gold
(199, 21, 133), # mediumvioletred
(0, 0, 205), # mediumblue
(222, 184, 135), # burlywood
(127, 255, 0), # chartreuse
(0, 255, 0), # lime
(0, 250, 154), # mediumspringgreen
(65, 105, 225), # royalblue
(220, 20, 60), # crimson
(0, 255, 255), # aqua
(0, 191, 255), # deepskyblue
(147, 112, 219), # mediumpurple
(0, 0, 255), # blue
(160, 32, 240), # purple3
(240, 128, 128), # lightcoral
(255, 99, 71), # tomato
(218, 112, 214), # orchid
(216, 191, 216), # thistle
(255, 0, 255), # fuchsia
(220, 130, 200), # palevioletred
(240, 230, 140), # khaki
(255, 255, 84), # laserlemon
(100, 149, 237), # cornflower
(221, 160, 221), # plum
(144, 238, 144), # lightgreen
(135, 206, 235), # skyblue
(255, 20, 147), # deeppink
(255, 160, 122), # lightsalmon
(175, 238, 238), # paleturquoise
(127, 255, 212), # aquamarine
(255, 105, 180), # hotpink
(255, 228, 196), # bisque
(255, 182, 193), # lightpink
(169, 169, 169), # darkgray
(220, 220, 220) # gainsboro
]
