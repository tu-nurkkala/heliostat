from scipy import stats

# Each pair is (Azimuth degree, string potentiometer reading).
data = ( (134.04, 413),
         (147.87, 444),
         (163.8, 474),
         (183.79, 520),
         (199.46, 552),
         (214.06, 596),
         (227.64, 636),
         (239.29, 667) )

x_vals = [ pair[0] for pair in data ]
y_vals = [ pair[1] for pair in data ]

slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)

print slope, intercept, r_value, p_value, std_err

# Prints
# 2.39960237277 84.8400496537 0.997133524996 5.87557462484e-08 0.0743340798749
