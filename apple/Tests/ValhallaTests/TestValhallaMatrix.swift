import XCTest
import ValhallaConfigModels
@testable import Valhalla

/// `sources_to_targets` for auto costing runs thor::CostMatrix, whose
/// ReachedMap patches/valhalla-costmatrix-no-pmr.patch changes.
final class TestValhallaMatrix: XCTestCase {
    var defaultConfig: ValhallaConfig!

    override func setUp() async throws {
        let tilesTarUrl = Bundle.module.url(forResource: "TestData/valhalla_tiles", withExtension: "tar")!
        defaultConfig = try ValhallaConfig(tileExtractTar: tilesTarUrl)
    }

    func testAutoMatrixRunsCostMatrix() throws {
        let valhalla = try Valhalla(defaultConfig)

        let response = try valhalla.matrix(rawRequest: """
            {"sources": [{"lat": 42.5063, "lon": 1.5218}, {"lat": 42.5086, "lon": 1.5394}],
             "targets": [{"lat": 42.5086, "lon": 1.5394}, {"lat": 42.5063, "lon": 1.5218}],
             "costing": "auto"}
            """)

        let json = try XCTUnwrap(
            JSONSerialization.jsonObject(with: Data(response.utf8)) as? [String: Any])
        XCTAssertEqual(json["algorithm"] as? String, "costmatrix")
        let rows = try XCTUnwrap(json["sources_to_targets"] as? [[[String: Any]]])
        XCTAssertEqual(rows.count, 2)
        for (i, row) in rows.enumerated() {
            XCTAssertEqual(row.count, 2)
            let other = try XCTUnwrap(row[i == 0 ? 0 : 1]["distance"] as? Double)
            let same = try XCTUnwrap(row[i == 0 ? 1 : 0]["distance"] as? Double)
            XCTAssertGreaterThan(other, 0.5, "\(response)")
            XCTAssertEqual(same, 0, accuracy: 0.001)
        }
    }

    /// The same actor answers a second matrix after the first one clears its maps.
    func testRepeatedMatrices() throws {
        let valhalla = try Valhalla(defaultConfig)
        let request = """
            {"sources": [{"lat": 42.5063, "lon": 1.5218}],
             "targets": [{"lat": 42.5086, "lon": 1.5394}], "costing": "auto"}
            """
        let first = try valhalla.matrix(rawRequest: request)
        let second = try valhalla.matrix(rawRequest: request)
        XCTAssertEqual(first, second)
    }
}
