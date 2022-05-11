def test_numpy():
  import numpy as np
  a = np.arange(15).reshape(3, 5)
  print(a)
  print('numpy: OK')
 
# define a main function
def test_pygame():
    # import the pygame module, so you can use it
    import pygame
     
    # initialize the pygame module
    pygame.init()
    # load and set the logo
    logo = pygame.image.load("logo32x32.png")
    pygame.display.set_icon(logo)
    pygame.display.set_caption("minimal program")
     
    # create a surface on screen that has the size of 240 x 180
    screen = pygame.display.set_mode((240,180))
     
    # define a variable to control the main loop
    running = True
     
    # main loop
    while running:
        # event handling, gets all event from the event queue
        for event in pygame.event.get():
            # only do something if the event is of type QUIT
            if event.type == pygame.QUIT:
                # change the value to False, to exit the main loop
                running = False
    print('pygame: OK')
     
def test_qiskit():
  import numpy as np
  from qiskit import QuantumCircuit, transpile
  from qiskit.providers.aer import QasmSimulator
  from qiskit.visualization import plot_histogram
  
  # Use Aer's qasm_simulator
  simulator = QasmSimulator()
  
  # Create a Quantum Circuit acting on the q register
  circuit = QuantumCircuit(2, 2)
  
  # Add a H gate on qubit 0
  circuit.h(0)
  
  # Add a CX (CNOT) gate on control qubit 0 and target qubit 1
  circuit.cx(0, 1)
  
  # Map the quantum measurement to the classical bits
  circuit.measure([0,1], [0,1])
  
  # compile the circuit down to low-level QASM instructions
  # supported by the backend (not needed for simple circuits)
  compiled_circuit = transpile(circuit, simulator)
  
  # Execute the circuit on the qasm simulator
  job = simulator.run(compiled_circuit, shots=1000)
  
  # Grab results from the job
  result = job.result()
  
  # Returns counts
  counts = result.get_counts(compiled_circuit)
  print("\nTotal count for 00 and 11 are:",counts)
  
  # Draw the circuit
  # circuit.draw(output='mpl')
  print(circuit)
  print('qsikit: OK')
              
# run the main function only if this module is executed as the main script
# (if you import this as a module then nothing is executed)
if __name__=="__main__":
    # call the main function
    test_numpy()
    test_qiskit()
    test_pygame()
    #main()
