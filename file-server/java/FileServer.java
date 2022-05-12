

import java.net.Socket;
import java.net.ServerSocket;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.io.FileInputStream;
import java.io.File;
import java.io.UnsupportedEncodingException;
import java.io.FileNotFoundException;
import java.net.InetAddress;

public class FileServer {
	private static class RequestHandler implements Runnable {
		private static class ByteBuffer {
			public byte[] buf;
			public int len;
			public ByteBuffer(byte[] buf, int len) {
				this.buf = buf;
				this.len = len;
			}
		};
		private Socket conn;
		private String directory;

		public RequestHandler(Socket conn, String directory) {
			this.conn = conn;
			this.directory = directory;
		}

		private static byte[] build_header(int code, int len) {
			String status = null;
			if (code == 200) {
				status = "OK";
			} else if (code == 404) {
				status = "Not Found";
			} else {
				throw new RuntimeException("badness");
			}
			String res = "HTTP/1.0 " + code + " " + status + "\r\n";
			res += "Content-Type: text/plain; charset=UTF-8\r\n";
			res += "Content-Length: " + len + "\r\n";
			res += "\r\n";
			byte[] ret = null;
			try {
				ret = res.getBytes("ascii");
			} catch (UnsupportedEncodingException e) {
				throw new RuntimeException(e);
			}
			return ret;
		}

		private ByteBuffer read_file(String path) {
			String[] parts = path.split("/");
			String filtered = "";
			for (int i = 1; i < parts.length; i++) {
				String p = parts[i];
				if (p.equals("..")) {
					continue;
				}
				filtered += "/" + p;
			}
			filtered = this.directory + filtered;
			File f = new File(filtered);
			try {
				//InputStream in = new FileInputStream(filtered);
				InputStream in = new FileInputStream(f);
				byte[] buf = new byte[(int) f.length()];
				int n = in.read(buf, 0, buf.length);
				if (n != buf.length) {
					throw new RuntimeException("read whole file read different amount of bytes");
				}
				return new ByteBuffer(buf, buf.length);
				/*
				byte[] buf = new byte[4096];
				int pos = 0;
				while (true) {
					int n = in.read(buf, pos, buf.length - pos);
					if (n < 0) {
						break;
					}
					pos += n;
					if (pos == buf.length) {
						byte[] buf2 = new byte[buf.length * 2];
						System.arraycopy(buf, 0, buf2, 0, buf.length);
						buf = buf2;
					} else if (pos > buf.length) {
						throw new RuntimeException("badness");
					}
				}
				return new ByteBuffer(buf, pos);
				*/
			} catch (FileNotFoundException e) {
				// pass
			} catch (IOException e) {
				throw new RuntimeException(e);
			}
			return null;
		}

		private void readall() {
			try {
				InputStream in = this.conn.getInputStream();
				byte[] buf = new byte[256];
				while (true) {
					int n = in.read(buf);
					if (n < 0) {
						break;
					}
				}
			} catch (IOException e) {
				throw new RuntimeException(e);
			}
		}

		@Override
		public void run() {
			try (
				BufferedReader in = new BufferedReader(
					new InputStreamReader(this.conn.getInputStream()));
			) {
				String line = in.readLine();
				String[] parts = line.split(" ");
				String path = parts[1];
				ByteBuffer data = this.read_file(path);
				byte[] header = null;
				if (data == null) {
					try {
						byte[] str = "Not Found.".getBytes("ascii");
						data = new ByteBuffer(str, str.length);
					} catch (UnsupportedEncodingException e) {
						throw new RuntimeException(e);
					}
					header = RequestHandler.build_header(404, data.len);
				} else {
					header = RequestHandler.build_header(200, data.len);
				}
				OutputStream out = this.conn.getOutputStream();
				out.write(header);
				out.write(data.buf, 0, data.len);
				this.readall();
				this.conn.close();
			} catch (IOException e) {
				System.out.print("[error] thread exception: " + e + "\n");
			}
		}
	}

	public static void main(String[] args) {
		try {
			ServerSocket serverSocket = new ServerSocket(Integer.parseInt(args[1]), 1025, InetAddress.getByName(args[0]));
			//ServerSocket serverSocket = new ServerSocket(Integer.parseInt(args[0]), 8, InetAddress.getLoopbackAddress());

			while (true) {
				Socket conn = serverSocket.accept();
				new Thread(new RequestHandler(conn, args[2])).start();
			}
		} catch (IOException e) {
			System.out.print("[error] main exception: " + e + "\n");
		}
	}
}
