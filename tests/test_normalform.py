from scipy.integrate import solve_ivp
from ssmlearnpy.utils import ridge

from ssmlearnpy import SSMLearn

from ssmlearnpy.reduced_dynamics.shift_or_differentiate import shift_or_differentiate
from ssmlearnpy.reduced_dynamics.normalform import NormalForm, NonlinearCoordinateTransform, create_normalform_initial_guess
from sklearn.preprocessing import PolynomialFeatures
from ssmlearnpy.utils.preprocessing import get_matrix , PolynomialFeaturesWithPattern
from ssmlearnpy.reduced_dynamics.normalform import NonlinearCoordinateTransform, NormalForm, create_normalform_transform_objective, prepare_normalform_transform_optimization, unpack_optimized_coeffs
from ssmlearnpy.geometry.coordinates_embedding import coordinates_embedding
from scipy.optimize import minimize, least_squares
import numpy as np
from scipy.io import savemat, loadmat

from ssmlearnpy.utils.preprocessing import complex_polynomial_features



def vectorfield(t,x, r = 1):
    # needed to test regression
    # damped duffing oscillator with fixed points at x=0 and x=+/-1.
    # x[0] is position, x[1] is velocity
    return np.array([x[1], x[0]-r*x[0]**3 - 0.1*x[1]])


# test normal form transforms:
def test_normalform_nonlinear_coeffs():
    linearpart = np.ones((2,2))
    nf = NormalForm(linearpart)
    nonlinear_coeffs = nf._nonlinear_coeffs(degree = 3)
    truecoeffs = np.array([[2, 1, 0, 3, 2, 1, 0], [0, 1, 2, 0, 1, 2, 3]])
    assert np.all(nonlinear_coeffs == truecoeffs)

def test_normalform_lincombinations():
    # use the linear part of the above vectorfield at -1, 0:
    linearpart = np.array([[-0.05 + 1j*1.41332940251026, 0], [0, -0.05 - 1j*1.41332940251026]])
    nf = NormalForm(linearpart)
    lincombs = nf._eigenvalue_lin_combinations(degree = 3)
    lamb = -0.05 + 1j*1.41332940251026
    lambconj = -0.05 - 1j*1.41332940251026
    true_lincombs = np.array([[-lamb, -lambconj, lamb - 2*lambconj, -2*lamb, -2*np.real(lamb), -2*lambconj, lamb-3*lambconj],
                              [lambconj-2*lamb, -lamb, -lambconj, lambconj-3*lamb, -2*lamb, -2*np.real(lamb), -2*lambconj]])
    assert np.allclose(lincombs, true_lincombs)
    
def test_normalform_resonance():
     # use the linear part of the above vectorfield at -1, 0:
    linearpart = np.array([[-0.05 - 1j*1.41332940251026, 0], [0, -0.05 + 1j*1.41332940251026]])
    nf = NormalForm(linearpart)
    resonances = nf._resonance_condition(degree = 3)
    whereistrue = np.where(resonances)
    assert np.allclose(whereistrue, [[0,1],[4,5]])



def test_nonlinear_change_of_coords():
    xx = np.linspace(-1, 1, 10)
    yy = np.linspace(-0.5, 0.5, 10)
    transformedx = xx+yy+xx**2+yy**2
    vect = np.array([xx, yy])
    #print(vect.shape)
    transformedy = xx-yy+xx**3-yy*xx
    poly_features= PolynomialFeatures(degree=3, include_bias=False).fit(vect.T)
    vect_transform = poly_features.transform(vect.T)
    #print(vect_transform.shape)
    exponents = poly_features.powers_.T
    #print(exponents)
    # (2, 10)
    # (10, 9)
    # [[1 0 2 1 0 3 2 1 0]
    # [0 1 0 1 2 0 1 2 3]]
    transformationCoeffs = np.array([[1,1, 1, 0, 1,0, 0,0,0], # x + y +x^2 +y^2
                                     [1, -1, 0, -1, 0, 1, 0, 0, 0]]) # x - y + x^3 - yx
    TF = NonlinearCoordinateTransform(2, 3, transform_coefficients=transformationCoeffs)
    z = TF.transform(vect.T)
    
    assert np.allclose(z[:,0], transformedx)
    assert np.allclose(z[:,1], transformedy)
    

def test_set_dynamics_and_transformation_structure():
    t = np.linspace(0, 10, 1000)
    dt = t[1] - t[0]
    ic_0 = np.array([0.1, 0])
    ic_1 = np.array([0.112, 0])
    sol_0 = solve_ivp(vectorfield, [t[0], t[-1]], ic_0, t_eval=t)
    sol_1 = solve_ivp(vectorfield, [t[0], t[-1]], ic_1, t_eval=t)
    trajectories = [sol_0.y - np.array([1,0]).reshape(-1,1), sol_1.y - np.array([1,0]).reshape(-1,1)]
    times = [t, t]
    X, y  = shift_or_differentiate(trajectories, times, 'flow') # get an estimate for the linear part
    # add the constraints to the fixed points explicitly
    constLHS = [[-1, 0]]
    constRHS = [[0, 0]]
    cons = [constLHS, constRHS]
    # Fit reduced model
    mdl = ridge.get_fit_ridge(X, y, poly_degree = 3, constraints = cons)
    linearPart = mdl.map_info['coefficients'][:,:2]
    nf = NormalForm(linearPart)
    nf.set_dynamics_and_transformation_structure('flow', 3)
    truestructure = [False, False, False, False, True, False, False]
    for s, t in zip(nf.dynamics_structure, truestructure):
        assert s == t


def test_prepare_normalform_transform_optimization():
    t = np.linspace(0, 10, 1000)
    dt = t[1] - t[0]
    ic_0 = np.array([0.1, 0])
    ic_1 = np.array([0.112, 0])
    sol_0 = solve_ivp(vectorfield, [t[0], t[-1]], ic_0, t_eval=t)
    sol_1 = solve_ivp(vectorfield, [t[0], t[-1]], ic_1, t_eval=t)
    trajectories = [sol_0.y - np.array([1,0]).reshape(-1,1), sol_1.y - np.array([1,0]).reshape(-1,1)]
    times = [t, t]
    X, y  = shift_or_differentiate(trajectories, times, 'flow') # get an estimate for the linear part
    # add the constraints to the fixed points explicitly
    constLHS = [[-1, 0]]
    constRHS = [[0, 0]]
    cons = [constLHS, constRHS]
    # Fit reduced model
    mdl = ridge.get_fit_ridge(X, y, poly_degree = 3, constraints = cons)
    linearPart = mdl.map_info['coefficients'][:,:2]
    _, nf, linerror, Transformation_normalform_polynomial_features, DTransformation_normalform_polynomial_features = prepare_normalform_transform_optimization( times, trajectories, linearPart)
    assert(DTransformation_normalform_polynomial_features[0].shape == (1000, 6))

def test_create_normalform_initial_guess():
    t = np.linspace(0, 10, 1000)
    dt = t[1] - t[0]
    ic_0 = np.array([0.1, 0])
    ic_1 = np.array([0.112, 0])
    sol_0 = solve_ivp(vectorfield, [t[0], t[-1]], ic_0, t_eval=t)
    sol_1 = solve_ivp(vectorfield, [t[0], t[-1]], ic_1, t_eval=t)
    trajectories = [sol_0.y - np.array([1,0]).reshape(-1,1), sol_1.y - np.array([1,0]).reshape(-1,1)]
    times = [t, t]
    X, y  = shift_or_differentiate(trajectories, times, 'flow') # get an estimate for the linear part
    # add the constraints to the fixed points explicitly
    constLHS = [[-1, 0]]
    constRHS = [[0, 0]]
    cons = [constLHS, constRHS]
    # Fit reduced model
    mdl = ridge.get_fit_ridge(X, y, poly_degree = 3, constraints = cons)
    linearPart = mdl.map_info['coefficients'][:,:2]
    _, nf, linerror, Transformation_normalform_polynomial_features, DTransformation_normalform_polynomial_features = prepare_normalform_transform_optimization( times, trajectories, linearPart)
    initial_guess = create_normalform_initial_guess(mdl, nf)
    assert len(initial_guess) == 14

def test_normalform_transform():
    t = np.linspace(0, 10, 1000)
    dt = t[1] - t[0]
    ic_0 = np.array([0.1, 0])
    ic_1 = np.array([0.112, 0])
    sol_0 = solve_ivp(vectorfield, [t[0], t[-1]], ic_0, t_eval=t)
    sol_1 = solve_ivp(vectorfield, [t[0], t[-1]], ic_1, t_eval=t)
    trajectories = [sol_0.y - np.array([1,0]).reshape(-1,1), sol_1.y - np.array([1,0]).reshape(-1,1)]
    times = [t, t]
    X, y  = shift_or_differentiate(trajectories, times, 'flow') # get an estimate for the linear part
    #print(X[0].shape)
    # add the constraints to the fixed points explicitly
    constLHS = [[-1, 0]]
    constRHS = [[0, 0]]
    cons = [constLHS, constRHS]
    # Fit reduced model
    mdl = ridge.get_fit_ridge(X, y, poly_degree = 5, constraints = cons)
    linearPart = mdl.map_info['coefficients'][:,:2]
    dictTosave = {}
    dictTosave['trajectories'] = trajectories
    dictTosave['times'] = times
    savemat('test_SSMLearn.mat', dictTosave)
    nf, n_unknowns_dynamics, n_unknowns_transformation, objectiv = create_normalform_transform_objective(times, trajectories, linearPart, degree = 5)
    initial_guess = create_normalform_initial_guess(mdl, nf)
    # # we can use the special sturcutre of the loss and use scipy.optimize.least_suqares()
    res = least_squares(objectiv, initial_guess)
    d = unpack_optimized_coeffs(res.x, 1, nf, n_unknowns_dynamics, n_unknowns_transformation)
    print(d['coeff_dynamics'])
    print(d['coeff_transformation'])
    print(res)

if __name__ == '__main__':
    test_normalform_nonlinear_coeffs()
    test_normalform_lincombinations()
    test_normalform_resonance()
    test_nonlinear_change_of_coords()
    test_set_dynamics_and_transformation_structure()
    test_prepare_normalform_transform_optimization()
    test_create_normalform_initial_guess()
    test_normalform_transform()