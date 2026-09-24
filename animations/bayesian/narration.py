"""Narration for the Bayesian error characterization and mitigation explainer.

Each segment is a list of sentences. `text` is the subtitle. `say` overrides it for
speech synthesis where symbols or acronyms need spoken words.
Numbers trace to ACM Trans. Quantum Comput. 4(2), 11 (2023), arXiv:2010.09188v6:
Tables 1-7, Sections 2-5, and Lemma 2.1.
"""

SEGMENTS = [
    ("problem", [
        dict(text="On today's quantum computers, gates sometimes flip a qubit by mistake and readout sometimes reports the wrong bit, so the measured output distribution differs from the ideal one."),
        dict(text="The error mitigation in this paper estimates the ideal distribution by inverting a model of the noise, and that model needs the device's error rates."),
        dict(text="Those rates are usually treated as fixed values, such as the vendor's daily calibration, and this paper infers their probability distributions with Bayesian methods instead."),
    ]),
    ("readout", [
        dict(text='The measurement error model gives each qubit two rates, m0 for reading 1 when the qubit is in state 0, and m1 for reading 0 when it is in state 1.',
             say='The measurement error model gives each qubit two rates, m zero for reading one when the qubit is in state zero, and m one for reading zero when it is in state one.'),
        dict(text='A 2 × 2 matrix of these rates maps the ideal outcome probabilities to the observed ones, and because the paper assumes independent readout errors, the n-qubit matrix is a tensor product of these matrices.',
             say='A two by two matrix of these rates maps the ideal outcome probabilities to the observed ones, and because the paper assumes independent readout errors, the n-qubit matrix is a tensor product of these matrices.'),
        dict(text='The filter inverts this map by least squares restricted to valid probability vectors, since a plain matrix inverse can return negative probabilities.'),
    ]),
    ("gate", [
        dict(text='For gate errors, the paper uses a bit-flip model in which each qubit is flipped after a gate with a probability called the gate error rate.'),
        dict(text='The model comes from earlier work that gave no direct proof.'),
        dict(text='This paper proves it for one gate and extends it to several gates that commute with X, where the errors damp each nonconstant Fourier coefficient of the output by a factor that shrinks with the number of gates m.',
             say='This paper proves it for one gate and extends it to several gates that commute with X, where the errors damp each non-constant [Fourier](/fˈʊɹiˌA/) coefficient of the output by a factor that shrinks with the number of gates m.'),
        dict(text='If the rate differs from one half, the linear system for the Fourier coefficients has a unique solution, and constrained least squares again keeps the recovered distribution valid.',
             say='If the rate differs from one half, the linear system for the [Fourier](/fˈʊɹiˌA/) coefficients has a unique solution, and constrained least squares again keeps the recovered distribution valid.'),
    ]),
    ("bayes", [
        dict(text='The rates are inferred from repeated runs of a short test circuit, using its probability of measuring 0 as the observed quantity.'),
        dict(text='The consistent Bayesian method draws parameter samples from a broad prior and pushes each one through the error model to predict that probability.'),
        dict(text="Each sample is kept with probability proportional to the observed density divided by the density of the prior predictions, both evaluated at that sample's prediction, so the predictions of the kept samples approximate the distribution of the data."),
        dict(text='For comparison, the paper also runs standard Bayesian inference with a Gaussian likelihood, sampled in Stan.'),
    ]),
    ("calibrate", [
        dict(text="For readout, a Hadamard gate on each of four qubits of IBM's 5-qubit ibmqx2 device ideally gives probability one half of measuring 0, and bit-flip or phase-flip errors in the gate leave that value unchanged, so in this model only readout error shifts it.",
             say="For readout, a [Hadamard](/hˈædəmˌɑɹd/) gate on each of four qubits of I B M's five-qubit device, I B M Q X two, ideally gives probability one half of measuring zero, and bit-flip or phase-flip errors in the gate leave that value unchanged, so in this model only readout error shifts it."),
        dict(text='The circuit ran 128 batches of 1024 shots, giving 128 estimates of that probability for every qubit.'),
        dict(text='The posterior mean readout error rates ranged from about 5% to 18%, and on three of the four qubits, reading 0 from state 1 was the more likely error.',
             say='The posterior mean readout error rates ranged from about five to eighteen percent, and on three of the four qubits, reading zero from state one was the more likely error.'),
        dict(text="Applied to the same 128 estimates used for the inference, filters built from the vendor's calibrated rates rarely returned one half, while filters built from the posteriors centered the corrected values on it."),
    ]),
    ("apply", [
        dict(text='The readout filters, built from posterior means, were then applied to other circuits.'),
        dict(text="For three-qubit entangled states, the consistent Bayesian filter raised tomography fidelity to 0.92–0.94 and beat Qiskit's filter, at 0.89–0.92, on every state.",
             say="For three-qubit entangled states, the consistent Bayesian filter raised tomography fidelity to between zero point nine two and zero point nine four, and beat [Qiskit's](/kˈɪskɪts/) filter, at zero point eight nine to zero point nine two, on every state."),
        dict(text="In a two-qubit Grover search whose ideal answer has probability 1, the raw probability was 0.67, Qiskit's filter and a filter from detector tomography both gave 0.71, and the consistent Bayesian filter gave 0.91.",
             say="In a two-qubit Grover search whose ideal answer has probability one, the raw probability was zero point six seven, [Qiskit's](/kˈɪskɪts/) filter and a filter from detector tomography both gave zero point seven one, and the consistent Bayesian filter gave zero point nine one."),
        dict(text='The same filters kept this ordering when the circuit was rerun up to 16 hours later.'),
        dict(text="In a QAOA Max-Cut example at hour 0, the consistent Bayesian filter raised the probability of an optimal cut from 0.58 raw to 0.70, against 0.60 for Qiskit's filter, 0.64 for detector tomography, and 0.89 in a noiseless simulator.",
             say="In a Q A O A max-cut example at hour zero, the consistent Bayesian filter raised the probability of an optimal cut from zero point five eight raw to zero point seven, against zero point six for [Qiskit's](/kˈɪskɪts/) filter, zero point six four for detector tomography, and zero point eight nine in a noiseless simulator."),
        dict(text='The consistent method did slightly better than standard Bayesian inference in these two examples, and the two were nearly equal on random two-qubit Clifford circuits.'),
    ]),
    ("gates", [
        dict(text='To infer a gate error rate together with the two readout rates, a test circuit applied the NOT gate 200 times to one qubit, whose ideal result is 0 with probability 1.',
             say='To infer a gate error rate together with the two readout rates, a test circuit applied the NOT gate 200 times to one qubit, whose ideal result is zero with probability one.'),
        dict(text='The consistent posterior mean gate error rate was about 0.005 on qubit 1 and 0.004 on qubit 2.',
             say='The consistent posterior mean gate error rate was about zero point zero zero five on qubit one, and zero point zero zero four on qubit two.'),
        dict(text='Predictions from the consistent posterior matched the shape of the data distribution, while the standard posterior matched only its mean.'),
        dict(text='After both error types were filtered from the same 128 estimates, the consistent posterior means recovered the exact value 1 more often than the standard ones, especially on qubit 2.',
             say='After both error types were filtered from the same 128 estimates, the consistent posterior means recovered the exact value one more often than the standard ones, especially on qubit two.'),
        dict(text="With 200 gates, the predicted output is far more sensitive to the gate error rate than to the readout rates, which may explain why readout rates from this circuit filtered the Grover data less well, 0.84 instead of 0.91, though still above Qiskit's filter and detector tomography.",
             say="With 200 gates, the predicted output is far more sensitive to the gate error rate than to the readout rates, which may explain why readout rates from this circuit filtered the Grover data less well, zero point eight four instead of zero point nine one, though still above [Qiskit's](/kˈɪskɪts/) filter and detector tomography."),
    ]),
    ("limits", [
        dict(text='The filter matrices have 2^n rows and columns, so their size grows exponentially with the number of measured qubits.',
             say='The filter matrices have two to the n rows and columns, so their size grows exponentially with the number of measured qubits.'),
        dict(text='The multi-gate model covers only bit-flip errors on gates that commute with X up to a global phase, so gate errors were inferred only in simple test circuits such as the 200-NOT circuit, and all experiments used one 5-qubit device.',
             say='The multi-gate model covers only bit-flip errors on gates that commute with X up to a global phase, so gate errors were inferred only in simple test circuits such as the 200 NOT circuit, and all experiments used one five-qubit device.'),
        dict(text='The readout model also assumes that errors on different qubits are independent.'),
    ]),
    ("close", [
        dict(text="Inferring error rates as distributions from a few test circuits, whose number is constant or linear in the qubit count, gave posterior-mean readout filters that outperformed Qiskit's filter and detector tomography in the Grover and QAOA tests on ibmqx2.",
             say="Inferring error rates as distributions from a few test circuits, whose number is constant or linear in the qubit count, gave posterior-mean readout filters that outperformed [Qiskit's](/kˈɪskɪts/) filter and detector tomography in the Grover and Q A O A tests on I B M Q X two."),
    ]),
]
