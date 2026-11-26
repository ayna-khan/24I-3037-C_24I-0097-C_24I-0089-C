"""python -m frontend [--master MASTER] [--port 8000] [--open]"""
import argparse
import webbrowser

from .server import make_server


def main():
    parser = argparse.ArgumentParser(description='The Lifeline Gazette')
    parser.add_argument('--master', default='MASTER', help='folder with the master CSV files')
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--open', action='store_true', help='open the page in the default browser')
    args = parser.parse_args()
    print('Indexing the master dataset (once per start)...', flush=True)
    with make_server(args.master, args.port) as server:
        url = f'http://127.0.0.1:{server.server_port}/'
        print(f'The Lifeline Gazette is on the stands: {url}  (Ctrl+C to stop)', flush=True)
        if args.open:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == '__main__':
    main()
