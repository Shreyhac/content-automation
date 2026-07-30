import Foundation
import Vision
import AppKit

// usage: facebox <dir-of-jpgs>
// emits normalised face box (top-left origin) + landmark-derived chin/crown estimates
let dir = CommandLine.arguments[1]
let fm = FileManager.default
let files = try fm.contentsOfDirectory(atPath: dir).filter { $0.hasSuffix(".jpg") }.sorted()

print("file,bx,by,bw,bh,cx,cy,contourTop,contourBot,contourLeft,contourRight")

for f in files {
    let url = URL(fileURLWithPath: dir).appendingPathComponent(f)
    guard let img = NSImage(contentsOf: url),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("\(f),NA,,,,,,,,,"); continue
    }
    let req = VNDetectFaceLandmarksRequest()
    req.revision = VNDetectFaceLandmarksRequestRevision3
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([req]) } catch { print("\(f),ERR,,,,,,,,,"); continue }
    guard let obs = (req.results)?.first else { print("\(f),NOFACE,,,,,,,,,"); continue }

    // Vision box: origin bottom-left, normalised
    let b = obs.boundingBox
    let bx = b.minX, bw = b.width, bh = b.height
    let byTop = 1.0 - b.maxY          // convert to top-left origin
    let cx = b.midX, cy = 1.0 - b.midY

    var cTop = Double.nan, cBot = Double.nan, cL = Double.nan, cR = Double.nan
    if let fc = obs.landmarks?.faceContour, fc.pointCount > 2 {
        // landmark points are normalised to the face bounding box
        let pts = fc.normalizedPoints
        let ys = pts.map { Double(b.minY) + Double($0.y) * Double(bh) }
        let xs = pts.map { Double(b.minX) + Double($0.x) * Double(bw) }
        cTop = 1.0 - ys.max()!
        cBot = 1.0 - ys.min()!
        cL = xs.min()!
        cR = xs.max()!
    }
    func fmt(_ d: Double) -> String { d.isNaN ? "NA" : String(format: "%.5f", d) }
    print("\(f),\(fmt(Double(bx))),\(fmt(Double(byTop))),\(fmt(Double(bw))),\(fmt(Double(bh))),\(fmt(Double(cx))),\(fmt(Double(cy))),\(fmt(cTop)),\(fmt(cBot)),\(fmt(cL)),\(fmt(cR))")
}
