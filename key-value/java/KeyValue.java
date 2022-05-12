

import java.net.Socket;
import java.net.ServerSocket;
import java.net.InetAddress;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.PrintWriter;
import java.io.IOException;
import java.lang.Thread;

public class KeyValue {
	private static class ServerThread extends Thread {
		private Socket client;
		private HashMap map;

		public ServerThread(HashMap map, Socket client) {
			this.map = map;
			this.client = client;
		}

		public void run() {
			System.out.print("[info] starting thread\n");
			try (
					BufferedReader in = new BufferedReader(
						new InputStreamReader(this.client.getInputStream()));
					PrintWriter out = new PrintWriter(this.client.getOutputStream());
			) {
				String cmd_len_buf;
				while ((cmd_len_buf = in.readLine()) != null) {
					if (cmd_len_buf.charAt(0) != '*') {
						throw new RuntimeException("[error] unknown start of command: " + cmd_len_buf);
					}
					int cmd_len = Integer.parseInt(cmd_len_buf.substring(1));

					String[] parts = new String[cmd_len];
					int i = 0;
					while (i < cmd_len) {
						String buf = in.readLine();
						if (buf.charAt(0) != '$') {
							throw new RuntimeException("[error] unknown start of command: " + buf);
						}
						parts[i] = in.readLine();
						if (parts[i].length() != Integer.parseInt(buf.substring(1))) {
							throw new RuntimeException("[error] bad read: " + buf + ", " + String.join(", ", parts));
						}
						i++;
					}

					String ret = null;
					switch (parts[0]) {
					case "GET":
						String value = this.map.get(parts[1]);
						if (value == null) {
							ret = "$-1\r\n";
						} else {
							ret = "$" + value.length() + "\r\n" + value + "\r\n";
						}
						break;
					case "SET":
						this.map.set(parts[1], parts[2]);
						ret = "+OK\r\n";
						break;
					default:
						System.out.print("[error] unknown client message: '" + String.join(", ", parts) + "'\n");
						continue;
					}
					out.print(ret);
					out.flush();
					//System.out.print("[info] cmd: " + String.join(", ", parts) + " ret: " + ret + "\n");
				}
				this.client.close();
			} catch (IOException e) {
				System.out.print("[error] thread exception: " + e + "\n");
			}
			System.out.print("[info] closing thread\n");
		}
	}

	// port size(bytes)
	public static void main(String args[]) {
		/*
		HashMap map = new HashMap(24 * 1024 * 1024);
		for (int i = 0; i < 2 * 1000 * 1000; i++) {
			map.set(Integer.toString(i), new String("xxx"));
		}
		map.dump();
		*/
		try {
			ServerSocket serverSocket = new ServerSocket(Integer.parseInt(args[1]), 1025, InetAddress.getByName(args[0]));
			//ServerSocket serverSocket = new ServerSocket(Integer.parseInt(args[0]), 8, InetAddress.getLoopbackAddress());
			HashMap map = new HashMap(Long.parseLong(args[2]) * 1024, Integer.parseInt(args[3]));

			while (true) {
				Socket client = serverSocket.accept();
				new ServerThread(map, client).start();
			}
		} catch (IOException e) {
			System.out.print("[error] main exception: " + e + "\n");
		}
	}
}
