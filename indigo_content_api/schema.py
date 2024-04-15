def preprocess(endpoints):
    for i, (path, path_regex, method, callback) in enumerate(endpoints):
        if path == '/{frbr_uri}':
            # adjust this endpoint so that drf-spectacular documents the LIST api, not the RETRIEVE api
            endpoints[i] = (path, path_regex, method, callback.cls.as_view({'get': 'list'}))
            break
    return endpoints
