# References

Authoritative sources used to select and verify the modelling approach.
Generic PCB blogs were not used as evidence for engineering claims.

1. Texas Instruments, "High-Speed Layout Guidelines," SCAA082A,
   revised August 2017. https://www.ti.com/lit/pdf/scaa082
   - Capacitive + inductive coupling act together; stripline vs
     microstrip FEXT behaviour.
2. Texas Instruments, "Reducing Noise on Microcomputer Buses,"
   Application Note 337. https://www.ti.com/lit/pdf/snla134
   - Edge rate (dV/dt, dI/dt), not clock frequency, drives coupling.
3. Texas Instruments, "High-Speed DSP Systems Design Reference Guide,"
   SPRU889, May 2005. https://www.ti.com/lit/ug/spru889/spru889.pdf
   - Transmission-line termination; spacing/plane-distance guidance.
4. Texas Instruments, "High-Speed PCB Layout for PCIe Gen 5," SNLA426,
   June 2023. https://www.ti.com/lit/an/snla426/snla426.pdf
   - Modern high-speed routing and reference-plane practice.
5. Bert Simonovich, "Coupled Transmission Lines and Crosstalk,"
   Signal Integrity Journal, August 9, 2022.
   https://www.signalintegrityjournal.com/articles/2722-coupled-transmission-lines-and-crosstalk
   - Even/odd-mode basis of the model; NEXT saturation length;
     FEXT as modal-velocity mismatch.
6. Eric Bogatin and Bert Simonovich, "Guard Traces: Love Them or
   Leave Them?" Signal Integrity Journal, September 5, 2019.
   https://signalintegrityjournal.com/articles/1341-guard-traces-love-them-or-leave-them
   - Why guard traces were excluded from the quantitative study.
7. Bill Hargin, "Your #1 Defense Against a Crosstalk Crisis,"
   Siemens EDA, July 10, 2025.
   https://blogs.sw.siemens.com/electronic-systems-design/2025/07/10/crosstalk/
   - Practical spacing/stackup framing; 3W treated as rule of thumb.
8. Eric Bogatin, *Signal and Power Integrity - Simplified*,
   3rd ed. (Pearson). Quasi-TEM coupled-line theory and the
   `L = mu0*eps0*inv(C0)` relationship used in `crosstalk_model.py`.
9. Rohde & Schwarz, "Automated Internal/External Cable and Connector
   Test Solution in Line With PCIe 5.0 and 6.0 Specifications."
   https://www.rohde-schwarz.com/us/applications/automated-internal-external-cable-and-connector-test-solution-in-line-with-pcie-5.0-and-6.0-specifications_56279-1602472.html
   - NEXT/FEXT as separately terminated channel measurements.

## Claims deliberately qualified or rejected

* "Stripline has no FEXT" - rejected as absolute; residual coupling
  remains in real asymmetric stackups.
* "3W spacing cuts crosstalk ~70 %" - rejected; rule of thumb only,
  no fixed percentage is quoted anywhere in this project.
* "Crosstalk is proportional to length" - qualified; FEXT-type peaks
  grow with length under uniform weak coupling while NEXT saturates.
  The length study reports what the model actually produces.
* Series termination as "edge-rate control" - corrected; its role is
  source matching/reflection suppression.
