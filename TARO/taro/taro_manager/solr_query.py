import os


class SolrQuery:
    """
    Builds custom solr query based on params passed in request.
    Assumes this is a findingaid search, but default findingaid=True
    in case we want to expand this in the future.
    """
    # defining valid parameters
    query_params = ['text']
    filter_params = ['title', 'title_exact', 'abstract', 'abstract_exact', 'digital', 'taro_identifier',
                        'taro_identifier_exact', 'repository', 'repository_exact', 'filename', 'filename_exact']
    multivalued_filter_params = ['languages', 'languages_exact', 'creators', 'creators_exact', 'start_dates',
                                    'start_dates_exact', 'end_dates', 'end_dates_exact', 'geographic_areas', 
                                    'geographic_areas_exact', 'subject_topics', 'subject_topics_exact', 
                                    'subject_persons', 'subject_persons_exact', 'subject_organizations', 
                                    'subject_organizations_exact', 'extent', 'extent_exact', 'genreforms',
                                    'genreforms_exact', 'inclusive_dates', 'inclusive_dates_exact',]
    custom_params = ['recent', 'sort_asc', 'sort_dsc']
    base_url = f"{os.environ.get('SOLR_URL')}{os.environ.get('SOLR_COLLECTION')}select/?"
    url = f'{base_url}'
    query = ''
    filters = ''

    def _in_quotations(self, string_value):
        if string_value.startswith('"') and string_value.endswith('"') and len(string_value) > 1:
            return True
        return False

    def _add_filter(self, param_key, param_value):
        if isinstance(param_value, list):
            for val in param_value:
                print(f'val is {val}')
                if self._in_quotations(val):
                    param_key = param_key + "_exact"
                    val = val.replace('"', "")
                    add_to_filters= f'fq={param_key}:"{val}"&'
                    self.filters = self.filters + add_to_filters
                elif "," in val:
                    list_of_values = val.split(',')
                    for subval in list_of_values:
                        add_to_filters= f'fq={param_key}:"{subval}"&'
                        self.filters = self.filters + add_to_filters
                else:
                    add_to_filters= f'fq={param_key}:"{val}"&'
                    self.filters = self.filters + add_to_filters
        else:
            if self._in_quotations(param_value):
                param_key = param_key + "_exact"
                param_value = param_value.replace('"', "")
                add_to_filters= f'fq={param_key}:"{param_value}"&'
                self.filters = self.filters + add_to_filters
            elif "," in param_value:
                list_of_values = param_value.split(',')
                for subval in list_of_values:
                    add_to_filters= f'fq={param_key}:"{subval}"&'
                    self.filters = self.filters + add_to_filters
            else:
                add_to_filters= f'fq={param_key}:"{param_value}"&'
                self.filters = self.filters + add_to_filters


    def _add_multivalue_filter(self, param_key, param_value):
        if isinstance(param_value, list):  # handling multivalues passed as a list
            for val in param_value:
                # we check if exact search before checking multiple values.
                # we do not support multi-valued exact searches, e.g., creators_exact=["this","that"]
                if self._in_quotations(val):
                    param_key = param_key + "_exact"
                    val = val.replace('"', "")
                    add_to_filters= f'fq={param_key}:"{val}"&'
                    self.filters = self.filters + add_to_filters
                elif "," in val:  # handling multivalues passed as a comma-separated string
                    list_of_values = val.split(',')
                    for subval in list_of_values:
                        add_to_filters= f'fq={param_key}:"{subval}"&'
                        self.filters = self.filters + add_to_filters
                else:
                    if self._in_quotations(val):
                        param_key = param_key + "_exact"
                        val = val.replace('"', "")
                    add_to_filters= f'fq={param_key}:"{val}"&'
                    self.filters = self.filters + add_to_filters
        else: 
            if "," in param_value:  # handling multivalues passed as a comma-separated string
                list_of_values = param_value.split(',')
                for val in list_of_values:
                    if self._in_quotations(val):
                        param_key = param_key + "_exact"
                        val = val.replace('"', "")
                    add_to_filters= f'fq={param_key}:"{val}"&'
                    self.filters = self.filters + add_to_filters
            else:
                if self._in_quotations(param_value):
                    param_key = param_key + "_exact"
                    param_value = param_value.replace('"', "")
                add_to_filters= f'fq={param_key}:"{param_value}"&'
                self.filters = self.filters + add_to_filters

    def _add_custom_filter(self, param_key, param_value):

            if param_key == "recent":  # only returns finding aids added in the last month
                self.filters = self.filters + f'fq=date_added:[NOW-1MONTH TO NOW]&'

            if param_key == "sort_asc":  # sorts specified field ascending
                if isinstance(param_value, list):
                    for val in param_value:
                        self.filters = self.filters + f'sort={val} asc&'
                else:
                    self.filters = self.filters + f'sort={param_value} asc&'

            elif param_key == "sort_dsc":  # sorts specified field descending
                if isinstance(param_value, list):
                    for val in param_value:
                        self.filters = self.filters + f'sort={val} desc&'
                else:
                    self.filters = self.filters + f'sort={param_value} desc&'

    def _set_query(self, param_key, param_value):
        if isinstance(param_value, list):
            for val in param_value:
                add_to_query = f'q={param_key}:{val}&'
                self.query = self.query + add_to_query
        else:
            add_to_query = f'q={param_key}:{param_value}&'
            self.query = self.query + add_to_query


    def build_query(self, params, frontend_request=False, findingaid=True):
        params = dict(params.lists())  # convert QueryDict to standard dict

        for param_key, param_value in params.items():

            if param_key in self.filter_params:
                self._add_filter(param_key, param_value)

            if param_key in self.multivalued_filter_params: 
                self._add_multivalue_filter(param_key, param_value)

            if param_key in self.custom_params:
                self._add_custom_filter(param_key, param_value)

            if param_key in self.query_params:
                self._set_query(param_key, param_value)

        self.url = self.url + self.filters  # add filters to url
        self.url = self.url + self.query  # add query to url

        if "q=text" not in self.url:
            self.url = self.url + "q=*:*&"

        if findingaid:
            self.url = self.url + f'fq=django_ct:"taro_manager.findingaid"&'  # limit by finding aid

        self.url = self.url + "wt=json&"  # set results in json format

        if frontend_request:
            # if request is from front-end, only return fields we need. improves performance
            self.url = self.url + "fl=title,abstract,repository,repository_name,filename,creators,start_dates,end_dates&"
        else:
            # return more thorough data for researchers/harvesters
            self.url = self.url + "fl=title,abstract,digital,repository,repository_name,filename,date_added,last_modified,languages,creators,\
                start_dates,end_dates,geographic_areas,subject_topics,subject_persons,subject_organizations,extents,genreforms,inclusive_dates,taro_identifier&"

        self.url = self.url + f"rows={os.environ.get('MAX_SEARCH_RESULTS', 10000)}"  # set limit to 10k results

        print(f'url is {self.url}')
        return self.url
