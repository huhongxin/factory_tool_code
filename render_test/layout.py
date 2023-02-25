SHOW_NODEID = '''
{
    "layout":
    {
        "background": {
            "bgColor": "WHITE",
            "enableButtonZone": false,
            "rectangle": {
                "strokeThickness": 1,
                "block": {
                    "x_percent": 0,
                    "y_percent": 0,
                    "w_percent": 100,
                    "h_percent": 100
                }
            }
        },
        "items": [
            { "type": "TEXT",
                "data": {
                    "id": "NODE_ID",
                    "text": "<NODE_ID>",
                    "textColor": "WHITE",
                    "textAlign": "CENTER",
                    "backgroundColor": "RED",
                    "font": "DDIN_24",
                    "block": { "x": 0, "y": 0, "w": 296, "h": 32 },
                    "offset": { "x": -4, "y": 0 }
                }
            },
            { "type": "TEXT",
                "data": {
                    "id": "BEIJING_TIME",
                    "text": "Fri, Jan 08 15:20",
                    "textColor": "BLACK",
                    "textAlign": "CENTER",
                    "backgroundColor": "WHITE",
                    "font": "DDIN_CONDENSED_32",
                    "block": { "x": 8, "y": 36, "w": 280, "h": 48 },
                    "offset": { "x": 0, "y": 0 }
                }
            },
            { "type": "TEXT",
                "data": {
                    "id": "SUCCESS_STA",
                    "text": "",
                    "textColor": "BLACK",
                    "textAlign": "CENTER",
                    "backgroundColor": "WHITE",
                    "font": "DDIN_CONDENSED_32",
                    "block": { "x": 8, "y": 84, "w": 280, "h": 38 },
                    "offset": { "x": 0, "y": 0 }
                }
            }
        ]
    }
}
'''