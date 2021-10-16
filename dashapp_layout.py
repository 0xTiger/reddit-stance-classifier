from dash import dcc
import pandas as pd
import plotly.graph_objects as go
from pushlib_utils import stancecolormap, stancemap


custom_font = dict(family="Courier New, monospace",
                    size=14,
                    color="#000000")

df = pd.read_pickle('preds.pkl')[:10000]
fig = go.Figure(data=[go.Scatter(x=df['h_pos'][df['actual'] == stance], 
                                y=df['v_pos'][df['actual'] == stance], 
                                mode='markers',
                                marker_color=stancecolormap.get(stance),
                                opacity=0.6,
                                name=stance)
                    for stance in sorted(stancemap.keys(), reverse=True)],

                layout=go.Layout(
                        # title='Stances',
                        margin=go.layout.Margin(l=0,r=0,b=8,t=8),
                        autosize=True,
                        plot_bgcolor="rgba(0, 10, 25, 0.3)", 
                        paper_bgcolor="rgba(0, 0, 0, 0)",
                        legend=dict(orientation='h', 
                                    font=custom_font,
                                    yanchor="top",
                                    y=1.1),
                        annotations=[
                                    dict(x=1.1*stancemap[stance][1],
                                            y=1.1*stancemap[stance][0],
                                            xref='x', yref='y',
                                            text=stance,
                                            showarrow=False,
                                            font=custom_font) 
                                    for stance in ['left', 'right', 'lib', 'auth']
                                    ]
                        ))

fig.update_xaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', range=[-1.1, 1.1], constrain='domain')
fig.update_yaxes(zeroline=True, zerolinewidth=2, zerolinecolor='black', range=[-1.1, 1.1], scaleanchor='x', constrain='range')

layout = dcc.Graph(id='stance-scatter',figure=fig, style={'height': '90vw'})
