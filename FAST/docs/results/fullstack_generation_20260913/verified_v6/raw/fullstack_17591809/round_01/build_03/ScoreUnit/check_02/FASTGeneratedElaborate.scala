//> using scala "2.13.12"
//> using dep "edu.berkeley.cs::chisel3:3.6.1"
//> using plugin "edu.berkeley.cs:::chisel3-plugin:3.6.1"
import chisel3.stage.{ChiselGeneratorAnnotation, ChiselStage}
object FASTGeneratedElaborate extends App {
  (new ChiselStage).execute(Array("--target-dir", args(0), "-X", "verilog"),
    Seq(ChiselGeneratorAnnotation(() => new ScoreUnit)))
}
