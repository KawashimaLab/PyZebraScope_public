
 
def setStyle_CSS():
    
    CSS_dict = \
    {
        'QWidget':
        {
            'background-color': '#dddddd',
        },
        'QLabel#label':
        {
            'color': '#888888',
            'background-color': '#444444',
            'font-weight': 'bold',
        },
        'QLabel#label:active':
        {
            'color': '#1d90cd',
        },
        'QPushButton#button':
        {
            'color': '#888888',
            'background-color': '#444444',
            'font-weight': 'bold',
            'border': 'none',
            'padding': '5px',
        },
        'QPushButton#button:active':
        {
            'color': '#ffffff',
        },
        'QPushButton#button:hover':
        {
            'color': '#1d90cd',
        }
    }
        
    stylesheet = ""
    for item in CSS_dict:
        stylesheet += item + "\n{\n"
        for attribute in CSS_dict[item]:
            stylesheet += "  " + attribute + ": " + CSS_dict[item][attribute] + ";\n"
        stylesheet += "}\n"
    return stylesheet