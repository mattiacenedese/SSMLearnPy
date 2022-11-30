import logging

import pandas as pd
import numpy as np
import plotly.graph_objects as go


def plot_xy(
        x1,
        y1,
        x2 = [],
        y2 = [],
        font_name = 'Helvetica', 
        font_size = 16,
        axes_labels = ['time [s]', 'x'],
        time_plot = False,
        plt_width = 0,  
        plt_height = 0,
        dict_margin = {}
    ):
    """
    2D plot of data
    """
    fig = go.Figure()
    x_max, x_min, y_max, y_min = 0, 0, 0, 0
    line_marker1 = dict(width=2)
    plt_font_color = '#101010'
    line_marker2 = dict(dash='dot', color=plt_font_color, width=2)
    for i_traj in range(len(x1)):
        fig.add_scatter(
            x = x1[i_traj], 
            y = y1[i_traj],
            mode='lines', 
            line=line_marker1, 
            opacity = 0.5,
            name='',
            showlegend=False
        )
        x_i_max, x_i_min = np.max(x1[i_traj]), np.min(x1[i_traj])
        y_i_max, y_i_min = np.max(y1[i_traj]), np.min(y1[i_traj])
        x_max, x_min = max([x_max, x_i_max]), min([x_min, x_i_min])
        y_max, y_min = max([y_max, y_i_max]), min([y_min, y_i_min])

    if bool(x2)==True:
        for i_traj in range(len(x2)):
            fig.add_scatter(
                x = x2[i_traj], 
                y = y2[i_traj],
                mode='lines', 
                line=line_marker2, 
                name='',
                showlegend=False
            )
    if time_plot == True:
        x_range = [x_min, x_max]
        y_range = [y_min-0.1*np.abs(y_min), y_max+0.1*np.abs(y_max)]
    else:
        x_range = [x_min-0.1*np.abs(x_min), x_max+0.1*np.abs(x_max)]
        y_range = [y_min-0.1*np.abs(y_min), y_max+0.1*np.abs(y_max)]
        
    fig.update_layout(autosize=True,
                    width=plt_width, height=plt_height,
                    margin=dict_margin, 
                    xaxis_title = axes_labels[0],
                    yaxis_title = axes_labels[1],
                    font_family = font_name,
                    font_color = plt_font_color, 
                    font_size = font_size,
                    xaxis_range = x_range,
                    yaxis_range = y_range
    )

    return fig

def plot_xyz(
        x1,
        y1,
        z1 = [],
        x2 = [],
        y2 = [],
        z2 = [],
        font_name = 'Helvetica', 
        font_size = 16,
        axes_labels = ['x', 'y', 'z'],
        plt_width = 0,  
        plt_height = 0,
        dict_margin = {},
        add_surface = False,
        surface_dict = {}
    ):
    """
    3D plot of data
    """
    fig = go.Figure()
    x_max, x_min, y_max, y_min, z_max, z_min = 0, 0, 0, 0, 0, 0
    plt_font_color = '#101010'
    if add_surface == True:
        line_marker1 = dict(color=plt_font_color, width=2)
        line_marker2 = dict(color='#7E7E7E', width=2)
        fig.add_surface(
        x=surface_dict['x_mesh'],
        y=surface_dict['y_mesh'],
        z=surface_dict['z_mesh'],
        surfacecolor=np.square(surface_dict['c_mesh']),
        opacity = 0.7,
        colorscale= 'agsunset', # surface_dict['colorscale'],
        showscale=False,
        showlegend=False
        )
    else:
        line_marker1 = dict(width=2)
        line_marker2 = dict(color=plt_font_color, width=2)

    for i_traj in range(len(x1)):
        fig.add_scatter3d(
            x = x1[i_traj], 
            y = y1[i_traj],
            z = z1[i_traj],
            mode='lines', 
            line=line_marker1, 
            name='',
            showlegend=False
        )
        x_i_max, x_i_min = np.max(x1[i_traj]), np.min(x1[i_traj])
        y_i_max, y_i_min = np.max(y1[i_traj]), np.min(y1[i_traj])
        z_i_max, z_i_min = np.max(z1[i_traj]), np.min(z1[i_traj])
        x_max, x_min = max([x_max, x_i_max]), min([x_min, x_i_min])
        y_max, y_min = max([y_max, y_i_max]), min([y_min, y_i_min])
        z_max, z_min = max([z_max, z_i_max]), min([z_min, z_i_min])

    if bool(x2)==True:
        for i_traj in range(len(x2)):
            fig.add_scatter3d(
                x = x2[i_traj], 
                y = y2[i_traj],
                z = z2[i_traj],
                mode='lines', 
                line=line_marker2, 
                name='',
                showlegend=False
            )

    x_range = [x_min-0.1*np.abs(x_min), x_max+0.1*np.abs(x_max)]
    y_range = [y_min-0.1*np.abs(y_min), y_max+0.1*np.abs(y_max)]
    z_range = [z_min-0.1*np.abs(z_min), z_max+0.1*np.abs(z_max)]   

    fig.update_layout(autosize=True,
                    width=plt_width, height=plt_height,
                    margin=dict_margin, 
                    scene=dict(
                        xaxis_title = axes_labels[0],
                        yaxis_title = axes_labels[1],
                        zaxis_title = axes_labels[2],
                        xaxis_range = x_range,
                        yaxis_range = y_range,
                        zaxis_range = z_range
                        ),
                    font_family = font_name,
                    font_color = plt_font_color, 
                    font_size = font_size,
    )

    return fig

def compute_surface(
    surface_function = [],
    idx_reduced_coordinates = [1, 2],
    transf_mesh_generation = 0,
    idx_observables = [1],
    mesh_step = 100
    ):

    r_vec = np.linspace(0, 1, mesh_step + 1)
    th_vec = np.linspace(0, 2*np.pi, mesh_step + 1)
    r_mesh, th_mesh = np.meshgrid(r_vec,th_vec)
    x_mesh, y_mesh = r_mesh*np.cos(th_mesh), r_mesh*np.sin(th_mesh)
    x_data = np.array([x_mesh.flatten(), y_mesh.flatten(),])
    x_reduced_surf = np.matmul(transf_mesh_generation,x_data)
    x_full_surf = surface_function(x_reduced_surf.T).T

    if len(idx_observables) == 1:
        x_vec = x_reduced_surf[idx_reduced_coordinates[0]-1,:]
        y_vec = x_reduced_surf[idx_reduced_coordinates[1]-1,:]
        z_vec = x_full_surf[idx_observables[0]-1,:]
    
    if len(idx_observables) == 3:
        x_vec = x_full_surf[idx_observables[0]-1,:]
        y_vec = x_full_surf[idx_observables[1]-1,:]
        z_vec = x_full_surf[idx_observables[2]-1,:]

    surface_dict = {}
    surface_dict['x_mesh'] = x_vec.reshape(r_mesh.shape)
    surface_dict['y_mesh'] = y_vec.reshape(r_mesh.shape)
    surface_dict['z_mesh'] = z_vec.reshape(r_mesh.shape)
    surface_dict['c_mesh'] = r_mesh/np.amax(r_mesh)

    return surface_dict   