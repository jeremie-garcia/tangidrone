import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
plt.ion()
class DynamicUpdate():
    #Suppose we know the x range
    min_x = 0
    max_x = 100

    def on_launch(self):
        #Set up plot
        self.figure = plt.figure() 
        self.ax = self.figure.add_subplot(projection = "3d")
        self.lines, = self.ax.plot([],[],[], 'o')
        #Autoscale on unknown axis and known lims on the other
        self.ax.set_autoscaley_on(True)
        self.ax.set_xlim3d(0, 50)
        self.ax.set_ylim3d(0, 50)
        self.ax.set_zlim3d(0, 50)
        self.xdata = []
        self.ydata = []
        self.zdata = []
        #Other stuff
        self.ax.grid()
        ...

    def on_running(self):
        #Update data (with the new _and_ the old points)
        self.lines.set_data_3d(self.xdata, self.ydata, self.zdata)
        #Need both of these in order to rescale
        self.ax.relim()
        self.ax.autoscale_view()
        #We need to draw *and* flush
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

    #Example
    def __call__(self, x, y, z):
        self.xdata.append(x)
        self.ydata.append(y)
        self.zdata.append(z)
        self.on_running()