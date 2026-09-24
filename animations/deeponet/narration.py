"""Narration for the Quantum DeepONet explainer.

Each segment is a list of sentences. `text` is the subtitle. `say` overrides it for
speech synthesis where symbols or acronyms need spoken words.
Numbers trace to Quantum 9, 1761 (2025): Tables 1-4, Sections 2.1-2.4 and 4.3, and Figs. 7-8.
"""

SEGMENTS = [
    ("operator", [
        dict(text="Uncertainty quantification and optimal experimental design solve the same partial differential equation many times, each time with a different input function."),
        dict(text="A neural operator learns the map from that input function to the solution, so a trained model answers each new case with one forward pass."),
        dict(text="For the antiderivative operator, the input is a function v and the output is its integral u."),
    ]),
    ("deeponet", [
        dict(text="DeepONet, a deep operator network, splits this map between two networks.",
             say="[DeepONet](/dˈipˌOnɛt/), a deep operator network, splits this map between two networks."),
        dict(text="A branch net reads the input function at fixed sensor points, and a trunk net reads the location where the solution is wanted."),
        dict(text="The prediction is the dot product of their outputs plus a bias."),
    ]),
    ("cost", [
        dict(text="Each layer computes σ(Wx + b), and multiplying an n-dimensional input by its weight matrix takes on the order of n² operations.",
             say="Each layer computes sigma of W x plus b, and multiplying an n-dimensional input by its weight matrix takes on the order of n squared operations."),
        dict(text="Quantum DeepONet performs this multiplication on a quantum circuit whose cost grows linearly with n, as n/δ² for an error δ in each output entry.",
             say="Quantum [DeepONet](/dˈipˌOnɛt/) performs this multiplication on a quantum circuit whose cost grows linearly with n, as n over delta squared, for an error delta in each output entry."),
    ]),
    ("encode", [
        dict(text="The circuit is built from reconfigurable beam splitter, or RBS, gates, which rotate the states 01 and 10 of two neighboring qubits by an angle θ and leave 00 and 11 unchanged.",
             say="The circuit is built from reconfigurable beam splitter, or R B S, gates, which rotate the states zero one and one zero of two neighboring qubits by an angle theta, and leave zero zero and one one unchanged."),
        dict(text="Unary encoding stores a normalized vector x on n qubits, with entry j of x as the amplitude of the state in which only qubit j is 1.",
             say="Unary encoding stores a normalized vector x on n qubits, with entry j of x as the amplitude of the state in which only qubit j is one."),
        dict(text="A data loader starts with the first qubit in state 1 and passes amplitude down a chain of n−1 RBS gates whose angles are computed from x.",
             say="A data loader starts with the first qubit in state one, and passes amplitude down a chain of n minus one R B S gates whose angles are computed from x."),
    ]),
    ("pyramid", [
        dict(text="The weight matrix W is built from n(n−1)/2 plane rotations whose angles are the trained parameters, so W is orthogonal, and each rotation becomes one RBS gate in a pyramid.",
             say="The weight matrix W is built from n times n minus one over two plane rotations whose angles are the trained parameters, so W is orthogonal, and each rotation becomes one R B S gate in a pyramid."),
        dict(text="Each gate mixes the amplitudes of two neighboring unary states, so the state stays unary, and after the last gate it holds y = Wx.",
             say="Each gate mixes the amplitudes of two neighboring unary states, so the state stays unary, and after the last gate it holds y equals W x."),
    ]),
    ("readout", [
        dict(text="The readout step, called tomography, uses an extra ancilla qubit that interferes the output with a uniform vector.",
             say="The readout step, called tomography, uses an extra [ancilla](/ænsˈɪlə/) qubit that interferes the output with a uniform vector."),
        dict(text="For each unary state j, the probabilities of the two ancilla outcomes differ by entry j of y divided by √n, which gives its sign, and one of the probabilities then gives its size.",
             say="For each unary state j, the probabilities of the two [ancilla](/ænsˈɪlə/) outcomes differ by entry j of y divided by root n, which gives its sign, and one of the probabilities then gives its size."),
        dict(text="About 1/δ² shots give an error of about δ in each entry, independent of n, and each shot runs a circuit of depth proportional to n, so a layer costs on the order of n/δ².",
             say="About one over delta squared shots give an error of about delta in each entry, independent of n, and each shot runs a circuit of depth proportional to n, so a layer costs on the order of n over delta squared."),
        dict(text="Every valid outcome is unary, so a shot such as 0110, with two qubits in state 1, is discarded as an error.",
             say="Every valid outcome is unary, so a shot such as zero one one zero, with two qubits in state one, is discarded as an error."),
    ]),
    ("network", [
        dict(text="Stacking quantum layers, with the bias and activation applied classically between them, gives a quantum orthogonal neural network, and these networks replace the branch and trunk nets."),
        dict(text="Training runs on a classical computer, using a classical orthogonal network with the same mathematical form."),
        dict(text="The trained angles are then loaded into the circuits, so the speedup applies to evaluation, and training costs about as much as for a standard network."),
    ]),
    ("results", [
        dict(text="In noiseless simulations with Qiskit, the circuits reproduced the test errors of the classically trained networks in every example.",
             say="In noiseless simulations with [Qiskit](/kˈɪskɪt/), the circuits reproduced the test errors of the classically trained networks in every example."),
        dict(text="The L2 relative errors were 0.49% and 0.84% for the antiderivative at two input smoothness levels, 2.25% for the advection equation, and 1.38% for Burgers' equation.",
             say="The L two relative errors were zero point four nine and zero point eight four percent for the antiderivative at two input smoothness levels, two point two five percent for the advection equation, and one point three eight percent for Burgers' equation."),
        dict(text="Classical DeepONets with similar numbers of parameters reached 1.91% and 1.05% on the last two.",
             say="Classical [DeepONets](/dˈipˌOnɛts/) with similar numbers of parameters reached one point nine one and one point zero five percent on the last two."),
        dict(text="With the smoothest inputs and the branch input reduced to 10 principal components, a physics-informed version trained on the equation residual without solution data reached 0.76% for the antiderivative and 0.95% for Poisson's equation.",
             say="With the smoothest inputs, and the branch input reduced to ten principal components, a physics-informed version trained on the equation residual without solution data reached zero point seven six percent for the antiderivative, and zero point nine five percent for [Poisson's](/pwɑsˈOnz/) equation."),
    ]),
    ("noise", [
        dict(text="With finite shots, the gap from the noiseless simulation shrank as one over the square root of the shot count."),
        dict(text="With depolarizing gate noise at λ = 0.002, on the scale of current IBM gate error rates, a small function-approximation network with 0.15% noiseless error reached about 20% error, even with non-unary shots discarded.",
             say="With depolarizing gate noise at lambda equals zero point zero zero two, on the scale of current I B M gate error rates, a small function-approximation network with zero point one five percent noiseless error reached about twenty percent error, even with non-unary shots discarded."),
        dict(text="A noise model of the ibm_brisbane device gave 14.4% for the same network.",
             say="A noise model of the I B M Brisbane device gave fourteen point four percent for the same network."),
        dict(text="In the antiderivative tests, discarding non-unary shots lowered the error substantially, but under gate noise it stayed well above the noiseless error."),
        dict(text="Over the tested sizes, the error grew quickly with network depth and little with width."),
        dict(text="In these simulations, wider networks therefore tolerated noise better than deeper ones."),
    ]),
    ("limits", [
        dict(text="Unary encoding needs one qubit per vector entry, which limits network width on current devices."),
        dict(text="The circuit depth grows linearly with n, beyond the logarithmic depth over which current noisy devices can produce entanglement."),
        dict(text="The tested noise models also leave out coherent noise and cross-talk."),
    ]),
    ("close", [
        dict(text="Quantum DeepONet trains an orthogonal DeepONet classically and evaluates each layer on a circuit whose cost grows linearly with the input dimension, and in noiseless simulation the circuits reproduce the errors of the classically trained network.",
             say="Quantum [DeepONet](/dˈipˌOnɛt/) trains an orthogonal [DeepONet](/dˈipˌOnɛt/) classically, and evaluates each layer on a circuit whose cost grows linearly with the input dimension, and in noiseless simulation the circuits reproduce the errors of the classically trained network."),
    ]),
]
