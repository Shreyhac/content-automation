import Foundation
import Vision
import AppKit
import CoreImage

// usage: crown <dir-of-jpgs>
// person-segmentation → topmost foreground row (crown of head) + head-band horizontal centre
let dir = CommandLine.arguments[1]
let fm = FileManager.default
let files = try fm.contentsOfDirectory(atPath: dir).filter { $0.hasSuffix(".jpg") }.sorted()
let ciCtx = CIContext()

print("file,crownY,headCX,headL,headR")

for f in files {
    let url = URL(fileURLWithPath: dir).appendingPathComponent(f)
    guard let img = NSImage(contentsOf: url),
          let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        print("\(f),NA,NA,NA,NA"); continue
    }
    let req = VNGeneratePersonSegmentationRequest()
    req.qualityLevel = .accurate
    req.outputPixelFormat = kCVPixelFormatType_OneComponent8
    let handler = VNImageRequestHandler(cgImage: cg, options: [:])
    do { try handler.perform([req]) } catch { print("\(f),ERR,,,"); continue }
    guard let pb = req.results?.first?.pixelBuffer else { print("\(f),NOMASK,,,"); continue }

    CVPixelBufferLockBaseAddress(pb, .readOnly)
    let w = CVPixelBufferGetWidth(pb), h = CVPixelBufferGetHeight(pb)
    let stride = CVPixelBufferGetBytesPerRow(pb)
    let base = CVPixelBufferGetBaseAddress(pb)!.assumingMemoryBound(to: UInt8.self)

    // topmost row with a run of >= 8 foreground pixels (kills speckle)
    var crown = -1
    var rowL = 0, rowR = 0
    for y in 0..<h {
        var run = 0, best = 0, bl = 0, br = 0, curL = 0
        for x in 0..<w {
            if base[y*stride + x] > 128 {
                if run == 0 { curL = x }
                run += 1
                if run > best { best = run; bl = curL; br = x }
            } else { run = 0 }
        }
        if best >= 8 { crown = y; rowL = bl; rowR = br; break }
    }
    // head band: crown .. crown + 22% of image height, widest extent
    var hl = w, hr = 0
    if crown >= 0 {
        let band = min(h - 1, crown + Int(Double(h) * 0.22))
        for y in crown...band {
            for x in 0..<w where base[y*stride + x] > 128 {
                if x < hl { hl = x }
                if x > hr { hr = x }
            }
        }
    }
    CVPixelBufferUnlockBaseAddress(pb, .readOnly)
    if crown < 0 { print("\(f),NOMASK,,,"); continue }
    let ny = Double(crown) / Double(h)
    let nl = Double(hl) / Double(w), nr = Double(hr) / Double(w)
    _ = rowL; _ = rowR
    print(String(format: "%@,%.5f,%.5f,%.5f,%.5f", f, ny, (nl+nr)/2, nl, nr))
}
