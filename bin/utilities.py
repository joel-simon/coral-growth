from coral_growth import Coral

def calculate_inouts(params):
    num_inputs = Coral.num_inputs + params.n_memory + params.n_signals +\
                 params.n_morphogens*(params.morphogen_thresholds - 1)

    num_outputs = Coral.num_outputs + params.n_memory + params.n_signals + params.n_morphogens
