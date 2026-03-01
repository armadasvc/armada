import base64
import asyncio
import time
import os
import subprocess
from billiard import Process, Queue
from mitmproxy import http
from mitmproxy.tools.dump import DumpMaster
from mitmproxy.options import Options
from urllib.parse import urlparse
import requests
import json
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse
import logging 



def _build_url_with_params(base_url: str, params: dict) -> str:
    if not isinstance(base_url, str):
        raise TypeError("base_url must be a string")

    if not isinstance(params, dict):
        raise TypeError("params must be a dict")

    parsed = urlparse(base_url)

    # already existing parameters
    query = dict(parse_qsl(parsed.query))

    for k, v in params.items():
        # ignore any falsy value
        if v:
            query[k] = str(v)

    new_query = urlencode(query, doseq=True)

    return urlunparse(parsed._replace(query=new_query))


def _get_value_or_default(value, default):
    """Return value if not None, otherwise return default."""
    return value if value is not None else default


def _load_config(config):
    """Load configuration from file path or return dict as-is.

    Args:
        config: Either a file path (str) to a JSON file or a dict

    Returns:
        dict: The configuration dictionary
    """
    if isinstance(config, str):
        with open(config, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)
    return config



class ProxyManager:
    def __init__(self,config_proxy=None):
        self.config_proxy = config_proxy
        self.upstream_proxy_enabled = 0
        self.upstream_provider =os.getenv("PROXY_PROVIDER_URL","http://127.0.0.1:5001")
        self.upstream_proxy_broker_type ="provider"
        self.proxy_process = None
        self.count_data_queue = None
        self.upstream_object = None
        self.modifiers_array = []
        self.retrievers_array = []
        self.modifiers_request_array = []
        if self.config_proxy:
            self._parse_config_proxy()

    def launch_proxy(self):
        self._clean_previous_local_proxy()
        time.sleep(0.3)

        if self.upstream_proxy_enabled:
            upstream_proxy_url = self.fetch_upstream_proxy()
        else:
            upstream_proxy_url = None
        
        self.set_data_queue()
            
        self.proxy_process = SubprocessedMitmProxy(
            upstream_proxy_url=upstream_proxy_url,
            count_data_queue=self.count_data_queue,
            upstream_proxy_enabled=self.upstream_proxy_enabled,
            modifiers_array = self.modifiers_array,
            retrievers_array=self.retrievers_array,
            modifiers_request_array=self.modifiers_request_array
        )
        self.proxy_process.start()
        return self

    def exit_local_proxy(self):
        self.proxy_process.terminate()

    def switch_upstream_proxy(self):
        self.exit_local_proxy()
        self.launch_proxy()

    def set_data_queue(self):
         self.count_data_queue = Queue()
         return self.count_data_queue
    
    def get_data_count(self):
         for _ in range(self.count_data_queue.qsize()):
             element = self.count_data_queue.get()
         return element

    def retrieve(self,queue_id):
        for retriever in self.retrievers_array:
            if retriever["queue_id"]==queue_id:
                for _ in range(retriever["queue"].qsize()):
                    element = retriever["queue"].get()
                return element
            
    def _clean_previous_local_proxy(self):
        result = subprocess.run(f"lsof -t -i:{8081}", shell=True, capture_output=True, text=True)
        if result.stdout.strip():
            pid = result.stdout.strip()            
            os.system(f"kill -9 {pid}")
        else:
            pass


    def _parse_config_proxy(self):
        self.config_proxy = _load_config(self.config_proxy) if isinstance(self.config_proxy, str) else self.config_proxy
        self.upstream_proxy_enabled = _get_value_or_default(self.config_proxy.get("upstream_proxy_enabled"), self.upstream_proxy_enabled)
        self.upstream_proxy_broker_type = _get_value_or_default(self.config_proxy.get("upstream_proxy_broker_type"), self.upstream_proxy_broker_type)

    def fetch_upstream_proxy(self):
            self.upstream_object = UpstreamProxyFetcher(self.upstream_provider,self.upstream_proxy_broker_type, self.config_proxy).fetch_proxy()
            return self.upstream_object["proxy_url"]
    
    def add_retriever(self,queue_id: str,retriever_function):
        queue = Queue()
        proxy_queue_dict = {"queue_id":queue_id,"queue":queue,"retriever_function":retriever_function}
        self.retrievers_array.append(proxy_queue_dict)
    
    def add_modifier(self,modifier_function):
        self.modifiers_array.append(modifier_function)
    
    def add_request_modifier(self,modifier_request_function):
        self.modifiers_request_array.append(modifier_request_function)

class SubprocessedMitmProxy(Process):


    def __init__(self, *, upstream_proxy_url: str, count_data_queue, upstream_proxy_enabled,modifiers_array,retrievers_array,modifiers_request_array):
        super().__init__()
        self.upstream_proxy_url = upstream_proxy_url
        self.count_data_queue = count_data_queue
        self.upstream_enabled = upstream_proxy_enabled
        self.modifiers_array = modifiers_array
        self.retrievers_array = retrievers_array
        self.modifiers_request_array = modifiers_request_array

    def run(self):
        asyncio.run(self.asyncio_run())

    async def asyncio_run(self):
        if self.upstream_enabled:
            # Non-blocking TLS error on some proxies
            logging.getLogger("mitmproxy").setLevel(logging.CRITICAL)
            logging.getLogger("mitmproxy.proxy").setLevel(logging.CRITICAL)
            upstream_mode = "upstream:http://"+self.upstream_proxy_url.split('@')[1]
            opts = Options(listen_port=8081, mode=[upstream_mode], 
                           ssl_insecure=True,
                           )
        else:
            opts = Options(listen_port=8081, ssl_insecure=True)
        master = DumpMaster(opts, with_termlog=False, with_dumper=False)
        master.addons.add(ProxyAddOn(self.upstream_proxy_url, self.count_data_queue, self.modifiers_array, self.retrievers_array, self.modifiers_request_array))
        await master.run()


class ProxyAddOn:
    def __init__(self, upstream_proxy_url, count_data_queue, modifiers_array,retrievers_array,modifiers_request_array):
        self.total_data = 0
        self.upstream_proxy_url = upstream_proxy_url
        self.count_data_queue = count_data_queue
        self.proxy_parsed_url = None
        self.modifiers_array = modifiers_array
        self.retrievers_array = retrievers_array
        self.modifiers_request_array = modifiers_request_array

    def http_connect_upstream(self, flow: http.HTTPFlow):
        self.proxy_parsed_url = urlparse(self.upstream_proxy_url)
        if self.proxy_parsed_url.username or self.proxy_parsed_url.password:
            credentials = f"{self.proxy_parsed_url.username}:{self.proxy_parsed_url.password}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            flow.request.headers["proxy-authorization"] = f"Basic {encoded_credentials}"

    def response(self, flow: http.HTTPFlow) -> None:

        #Data Count
        if flow.response:
            content_length = flow.response.headers.get('Content-Length')
            if content_length:
                 self.total_data += int(content_length)
                 self.count_data_queue.put(self.total_data)

        #Executing retrievers
        for j in self.retrievers_array:
            j["retriever_function"](flow, j["queue"])

        
        #Executing modifiers
        for i in self.modifiers_array:
            i(flow)

    def request(self, flow: http.HTTPFlow) -> None:
        for i in self.modifiers_request_array:
            i(flow)
        
class UpstreamProxyFetcher:
    def __init__(self, provider, upstream_proxy_broker_type, proxy_config):
        self.provider = provider
        self.upstream_proxy_broker_type = upstream_proxy_broker_type
        self.proxy_config = proxy_config

    def fetch_proxy(self):
        if self.upstream_proxy_broker_type == "provider":
            url = _build_url_with_params(self.provider+"/fetch_proxy",self.proxy_config)
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
            else:
                raise Exception(f"Request failed with status code {response.status_code}")
        elif self.upstream_proxy_broker_type == "direct":
            result = {"proxy_url":self.provider}
        return result


    
                

