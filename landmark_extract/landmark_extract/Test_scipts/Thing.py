import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Assuming CubicSplineSurface is already defined or imported
class CubicSplineSurface: 
    def __init__(self, **kwargs):
        # Parameters
        knot_space = kwargs['knot_space'] if 'knot_space' in kwargs else .05
        surface_size = kwargs['surface_size'] if 'surface_size' in kwargs else np.array([10.,10.]) 

        # Spline Surface parameters
        self.degree = 3
        self.knot_space = knot_space
        self.grid_size = np.ceil(surface_size/knot_space+self.degree).astype(int).reshape([2,1]) 
        self.grid_center = np.ceil((self.grid_size-self.degree)/2).reshape(2,1) + self.degree - 1  
        self.ctrl_pts =  np.ones((self.grid_size[0,0], self.grid_size[1,0]) ).flatten()

        # Bounds
        self.map_lower_limits = (self.degree - self.grid_center)*self.knot_space
        self.map_upper_limits = (self.grid_size-self.grid_center+1)*self.knot_space          

    """ Compute spline coefficient index associated to the sparse representation """
    def compute_sparse_spline_index(self, tau, origin):
        mu    = -(np.ceil(-tau/self.knot_space).astype(int)) + origin
        c = np.zeros([len(tau),(self.degree+1)],dtype='int')
        for i in range(0, self.degree+1):
            c[:,i] = mu-self.degree+i
        return c
        
    """ Compute spline tensor coefficient index associated to the sparse representation """
    def compute_sparse_tensor_index(self, pts):
        # Compute spline along each axis
        cx = self.compute_sparse_spline_index(pts[0,:], self.grid_center[0,0])
        cy = self.compute_sparse_spline_index(pts[1,:], self.grid_center[1,0])

        # Kronecker product for index
        c = np.zeros([cx.shape[0],(self.degree+1)**2],dtype='int')
        for i in range(0, self.degree+1):
            for j in range(0, self.degree+1):
                c[:,i*(self.degree+1)+j] = cy[:,i]*(self.grid_size[0,0])+cx[:,j]
        return c

    """"Compute spline coefficients up to order 2 """
    def compute_sparse_tensor_coefficents(self, tau, origin, ORDER=0x01):
        nb_pts = len(tau)
        tau_bar = (tau/self.knot_space + origin) % 1 
        tau_3 = tau_bar + 3
        tau_2 = tau_bar + 2        
        tau_1 = tau_bar + 1
        tau_0 = tau_bar
        
        # Spline
        b = db = dbb = []
        if ORDER & 0x01:
            b = np.zeros([nb_pts,self.degree+1])
            b[:,0] = (1./6)*(-tau_3**3 + 12*tau_3**2 - 48*tau_3 + 64) 
            b[:,1] = (1./6)*(3*tau_2**3 - 24*tau_2**2 + 60*tau_2 - 44)
            b[:,2] = (1./6)*(-3*tau_1**3 + 12*tau_1**2 - 12*tau_1 + 4)
            b[:,3] = (1./6)*(tau_0**3)

        # 1st derivative of spline
        if ORDER & 0x02:
            db = np.zeros([nb_pts,self.degree+1])
            db[:,0] = (1./6)*(-3*tau_3**2 + 24*tau_3 - 48 ) * (1./self.knot_space) 
            db[:,1] = (1./6)*(9*tau_2**2 - 48*tau_2 + 60 ) * (1./self.knot_space)
            db[:,2] = (1./6)*(-9*tau_1**2 + 24*tau_1 - 12) * (1./self.knot_space)
            db[:,3] = (1./6)*(3*tau_0**2) * (1./self.knot_space)

        # 2nd derivative of spline
        if ORDER & 0x04:
            ddb = np.zeros([nb_pts,self.degree+1])
            ddb[:,0] = (1./6)*(-6*tau_3 + 24) * (1./self.knot_space**2)
            ddb[:,1] = (1./6)*(18*tau_2 - 48) * (1./self.knot_space**2)
            ddb[:,2] = (1./6)*(-18*tau_1 + 24) * (1./self.knot_space**2)
            ddb[:,3] = (1./6)*(6*tau_0) * (1./self.knot_space**2)

        return b, db, dbb


    def compute_tensor_spline(self, pts, ORDER=0x01):
        # Storing number of points
        nb_pts = pts.shape[1]

        # Compute spline along each axis
        bx, dbx, _ = self.compute_sparse_tensor_coefficents(pts[0,:], self.grid_center[0,0], ORDER | 0x01)
        by, dby, _ = self.compute_sparse_tensor_coefficents(pts[1,:], self.grid_center[1,0], ORDER | 0x01)

        # Compute spline tensor
        B = dBx = dBy = []
        if ORDER & 0x01:
            B = np.zeros([nb_pts,(self.degree+1)**2])
            for i in range(0,self.degree+1):
                for j in range(0,self.degree+1):           
                    B[:,i*(self.degree+1)+j] = by[:,i]*bx[:,j]


        if ORDER & 0x02:
            dBx = np.zeros([nb_pts,(self.degree+1)**2])
            dBy = np.zeros([nb_pts,(self.degree+1)**2])        
            for i in range(0,self.degree+1):
                for j in range(0,self.degree+1):           
                    dBx[:,i*(self.degree+1)+j] = by[:,i]*dbx[:,j]
                    dBy[:,i*(self.degree+1)+j] = dby[:,i]*bx[:,j]
            return B, dBx, dBy

        return B, dBx, dBy

def visualize_cubic_spline_surface():
    # Create an instance of CubicSplineSurface
    spline_surface = CubicSplineSurface(knot_space=0.5, surface_size=np.array([10., 10.]))
    
    # Generate a grid of points for evaluation
    x = np.linspace(-5, 5, 100)
    y = np.linspace(-5, 5, 100)
    X, Y = np.meshgrid(x, y)
    points = np.vstack([X.flatten(), Y.flatten()])
    
    # Compute the spline values at the grid points
    B, _, _ = spline_surface.compute_tensor_spline(points, ORDER=0x01)
    Z = B.dot(spline_surface.ctrl_pts).reshape(X.shape)  # Apply control points to compute the surface height
    
    # Plot the spline surface
    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(X, Y, Z, cmap='viridis', edgecolor='k', alpha=0.8)
    
    # Add control points for reference
    ctrl_pts_grid_x = np.arange(spline_surface.map_lower_limits[0], spline_surface.map_upper_limits[0], spline_surface.knot_space)
    ctrl_pts_grid_y = np.arange(spline_surface.map_lower_limits[1], spline_surface.map_upper_limits[1], spline_surface.knot_space)
    ctrl_pts_X, ctrl_pts_Y = np.meshgrid(ctrl_pts_grid_x, ctrl_pts_grid_y)
    ctrl_pts_Z = spline_surface.ctrl_pts.reshape(ctrl_pts_X.shape)
    ax.scatter(ctrl_pts_X, ctrl_pts_Y, ctrl_pts_Z, color='red', label='Control Points')

    # Customize the plot
    ax.set_title("Cubic Spline Surface", fontsize=16)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ax.legend()
    plt.show()

# Run the visualization
visualize_cubic_spline_surface()
