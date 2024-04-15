def preprocess(endpoints):
    for i, (path, path_regex, method, callback) in enumerate(endpoints):
        if path == '/{frbr_uri}':
            endpoints[i] = (path, path_regex, method, callback.cls.as_view({'get': 'list'}))
            break
    return endpoints
