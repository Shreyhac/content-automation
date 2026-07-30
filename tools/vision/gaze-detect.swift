import Foundation
import Vision
import AppKit

// usage: gaze <dir-of-jpgs>
let dir = CommandLine.arguments[1]
let fm = FileManager.default
let files = try fm.contentsOfDirectory(atPath: dir).filter { $0.hasSuffix(".jpg") }.sorted()

print("file,pitch,yaw,roll,eyeOpenL,eyeOpenR,eyeMidY,browEyeGap")

for f in files {
    let url = URL(fileURLWithPath: dir).appendingPathComponent(f)
    guard let img = NSImage(contentsOf: url),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("\(f),NA,NA,NA,NA,NA,NA,NA"); continue
    }
    let req = VNDetectFaceLandmarksRequest()
    req.revision = VNDetectFaceLandmarksRequestRevision3
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([req]) } catch { print("\(f),ERR,,,,,,"); continue }

    guard let obs = (req.results)?.first else {
        print("\(f),NOFACE,,,,,,"); continue
    }

    let pitch = obs.pitch?.doubleValue ?? Double.nan
    let yaw   = obs.yaw?.doubleValue ?? Double.nan
    let roll  = obs.roll?.doubleValue ?? Double.nan

    func openness(_ r: VNFaceLandmarkRegion2D?) -> Double {
        guard let r = r, r.pointCount > 2 else { return Double.nan }
        let pts = r.normalizedPoints
        let ys = pts.map { Double($0.y) }, xs = pts.map { Double($0.x) }
        let h = (ys.max()! - ys.min()!), w = (xs.max()! - xs.min()!)
        return w > 0 ? h / w : Double.nan
    }
    func midY(_ r: VNFaceLandmarkRegion2D?) -> Double {
        guard let r = r, r.pointCount > 0 else { return Double.nan }
        let ys = r.normalizedPoints.map { Double($0.y) }
        return ys.reduce(0,+) / Double(ys.count)
    }

    let lm = obs.landmarks
    let oL = openness(lm?.leftEye), oR = openness(lm?.rightEye)
    let eyeY = (midY(lm?.leftEye) + midY(lm?.rightEye)) / 2.0
    let browY = (midY(lm?.leftEyebrow) + midY(lm?.rightEyebrow)) / 2.0
    let gap = browY - eyeY

    func fmt(_ d: Double) -> String { d.isNaN ? "NA" : String(format: "%.4f", d) }
    print("\(f),\(fmt(pitch)),\(fmt(yaw)),\(fmt(roll)),\(fmt(oL)),\(fmt(oR)),\(fmt(eyeY)),\(fmt(gap))")
}
