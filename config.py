import argparse
import ssl


class Config:
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-a', '--hostname', help='pxGrid controller host name (multiple ok)', action='append')
        parser.add_argument('-n', '--nodename', help='Client node name')
        parser.add_argument('-w', '--password', help='Password (optional)')
        parser.add_argument('-d', '--description',
                            help='Description (optional)')
        parser.add_argument('--sgt',
                            help='filter on SGT (optional)')
        parser.add_argument('--email-server',
                            help='email server (optional)')
        parser.add_argument('--email-user',
                            help='email user (optional)')
        parser.add_argument(
            '-c', '--clientcert', help='Client certificate chain pem filename (optional)')
        parser.add_argument('-k', '--clientkey',
                            help='Client key filename (optional)')
        parser.add_argument('-p', '--clientkeypassword',
                            help='Client key password (optional)')
        parser.add_argument('-s', '--servercert',
                            help='Server certificates pem filename')
        self.config = parser.parse_args()

    def get_host_name(self):
        return self.config.hostname

    def get_node_name(self):
        return self.config.nodename

    def get_password(self):
        if self.config.password is not None:
            return self.config.password
        else:
            return ''

    def get_description(self):
        return self.config.description

    def get_sgt(self):
        return self.config.sgt

    def get_email_server(self):
       return self.config.email_server

    def get_email_user(self):
       return self.config.email_user

    def get_ssl_context(self):
        context = ssl.create_default_context()
        # adam hack
        gcontext = ssl.SSLContext()
        return gcontext

        # end of hack
        if self.config.clientcert is not None:
            context.load_cert_chain(certfile=self.config.clientcert,
                                    keyfile=self.config.clientkey,
                                    password=self.config.clientkeypassword)
        context.load_verify_locations(cafile=self.config.servercert)
        return context
