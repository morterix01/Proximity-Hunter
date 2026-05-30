import Foundation

enum APIConfig {
    /// Point at your backend. Simulator can reach a Mac-local server via localhost;
    /// a physical device needs the machine's LAN IP or a tunnel.
    static let baseURL = URL(string: "http://localhost:8000")!
}

enum APIError: Error, LocalizedError {
    case badStatus(Int)
    case decoding(Error)
    case transport(Error)

    var errorDescription: String? {
        switch self {
        case .badStatus(let c): return "Server error (\(c))"
        case .decoding:         return "Could not read server response"
        case .transport(let e): return e.localizedDescription
        }
    }
}

actor NetworkManager {
    static let shared = NetworkManager()

    private let session: URLSession = .shared
    private let decoder: JSONDecoder = {
        let d = JSONDecoder()
        d.dateDecodingStrategy = .custom { decoder in
            let s = try decoder.singleValueContainer().decode(String.self)
            if let date = NetworkManager.iso.date(from: s) { return date }
            if let date = NetworkManager.isoPlain.date(from: s) { return date }
            throw DecodingError.dataCorrupted(
                .init(codingPath: decoder.codingPath, debugDescription: "Bad date: \(s)")
            )
        }
        return d
    }()

    private static let iso: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()
    private static let isoPlain: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    // GET /api/deals
    func fetchDeals(store: Store? = nil) async throws -> [Deal] {
        var comps = URLComponents(
            url: APIConfig.baseURL.appendingPathComponent("api/deals"),
            resolvingAgainstBaseURL: false
        )!
        if let store { comps.queryItems = [URLQueryItem(name: "store", value: store.rawValue)] }
        return try await get([Deal].self, url: comps.url!)
    }

    // POST /api/device/register
    func registerDevice(token: String) async throws {
        let url = APIConfig.baseURL.appendingPathComponent("api/device/register")
        var req = URLRequest(url: url)
        req.httpMethod = "POST"
        req.setValue("application/json", forHTTPHeaderField: "Content-Type")
        req.httpBody = try JSONSerialization.data(
            withJSONObject: ["fcm_token": token, "platform": "ios"]
        )
        _ = try await send(req)
    }

    // MARK: - helpers

    private func get<T: Decodable>(_ type: T.Type, url: URL) async throws -> T {
        let data = try await send(URLRequest(url: url))
        do { return try decoder.decode(T.self, from: data) }
        catch { throw APIError.decoding(error) }
    }

    private func send(_ request: URLRequest) async throws -> Data {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else { throw APIError.badStatus(-1) }
            guard (200..<300).contains(http.statusCode) else {
                throw APIError.badStatus(http.statusCode)
            }
            return data
        } catch let e as APIError {
            throw e
        } catch {
            throw APIError.transport(error)
        }
    }
}
