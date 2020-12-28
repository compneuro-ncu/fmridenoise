def profiler_callback(node, status):
    from nipype.utils.profiler import log_nodes_cb
    if status != 'end':
        return
    if isinstance(node.result.runtime, list):
        return
    return log_nodes_cb(node, status)