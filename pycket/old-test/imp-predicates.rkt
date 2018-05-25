#lang pycket #:stdlib

(require (only-in '#%kernel chaperone-procedure impersonate-procedure))

;; Some test cases for chaperone-of? and impersonator-of? operations

(define test-vector
  (make-vector 1000))

(define imp-vector
  (impersonate-vector test-vector
    (lambda (vec i v) v)
    (lambda (vec i v) v)))

(define chp-vector
  (chaperone-vector test-vector
    (lambda (vec i v) v)
    (lambda (vec i v) v)))

(define test-proc
  (lambda (x)
    (+ x 5)))

(define chp-proc
  (chaperone-procedure
    test-proc
    (lambda (x)
      (unless (> x 0)
        (error 'chp-proc "Value less than zero"))
      (values
        x
        (lambda (res)
          (unless (> res 0)
            (error 'chp-proc "Result less than zero"))
          res)))))

(define imp-proc
  (impersonate-procedure
    test-proc
    (lambda (x)
      (unless (> x 0)
        (error 'imp-proc "Value less than zero"))
      (values
        x
        (lambda (res)
          (unless (> res 0)
            (error 'imp-proc "Result less than zero"))
          res)))))

(define test-box (box 5))

(define chp-box
  (chaperone-box test-box
    (lambda (a b) b)
    (lambda (a b) b)))

(define imp-box
  (impersonate-box test-box
    (lambda (a b) b)
    (lambda (a b) b)))

(define assert
  (lambda (v)
    (unless v
      (error 'imp-predicates "Assertion violation"))))

(printf "~nchaperone-of? procedure examples~n")
(printf "test-proc ? imp-proc  => ~s = #f ~n" (chaperone-of? test-proc imp-proc))
(printf "imp-proc  ? test-proc => ~s = #f ~n" (chaperone-of? imp-proc test-proc))
(printf "chp-proc  ? test-proc => ~s = #t ~n" (chaperone-of? chp-proc test-proc))
(printf "test-proc ? chp-proc  => ~s = #f ~n" (chaperone-of? test-proc chp-proc))

(assert (not (chaperone-of? test-proc imp-proc)))
(assert (not (chaperone-of? imp-proc test-proc)))
(assert (chaperone-of? chp-proc test-proc))
(assert (not (chaperone-of? test-proc chp-proc)))

(printf "~nimpersonator-of? procedure examples~n")
(printf "test-proc ? chp-proc  => ~s = #f ~n" (impersonator-of? test-proc chp-proc))
(printf "test-proc ? imp-proc  => ~s = #f ~n" (impersonator-of? test-proc imp-proc))
(printf "chp-proc  ? test-proc => ~s = #t ~n" (impersonator-of? chp-proc test-proc))
(printf "imp-proc  ? test-proc => ~s = #t ~n" (impersonator-of? imp-proc test-proc))
(printf "imp-proc  ? sub1      => ~s = #f ~n" (impersonator-of? imp-proc sub1))
(printf "sub1      ? imp-proc  => ~s = #f ~n" (impersonator-of? sub1 imp-proc))

(assert (not (impersonator-of? test-proc chp-proc)))
(assert (not (impersonator-of? test-proc imp-proc)))
(assert (impersonator-of? chp-proc test-proc))
(assert (impersonator-of? imp-proc test-proc))
(assert (not (impersonator-of? imp-proc sub1)))
(assert (not (impersonator-of? sub1 imp-proc)))

(printf "~nchaperone-of? vector examples~n")
(printf "test-vector ? imp-vector  => ~s = #f ~n" (chaperone-of? test-vector imp-vector))
(printf "imp-vector  ? test-vector => ~s = #f ~n" (chaperone-of? imp-vector test-vector))
(printf "chp-vector  ? test-vector => ~s = #t ~n" (chaperone-of? chp-vector test-vector))
(printf "test-vector ? chp-vector  => ~s = #f ~n" (chaperone-of? test-vector chp-vector))

(assert (not (chaperone-of? test-vector imp-vector)))
(assert (not (chaperone-of? imp-vector test-vector)))
(assert (chaperone-of? chp-vector test-vector))
(assert (not (chaperone-of? test-vector chp-vector)))

(printf "~nimpersonator-of? vector examples~n")
(printf "test-vector ? chp-vector  => ~s = #f ~n" (impersonator-of? test-vector chp-vector))
(printf "test-vector ? imp-vector  => ~s = #f ~n" (impersonator-of? test-vector imp-vector))
(printf "chp-vector  ? test-vector => ~s = #t ~n" (impersonator-of? chp-vector test-vector))
(printf "imp-vector  ? test-vector => ~s = #t ~n" (impersonator-of? imp-vector test-vector))
(printf "imp-vector  ? sub1        => ~s = #f ~n" (impersonator-of? imp-vector sub1))
(printf "sub1        ? imp-vector  => ~s = #f ~n" (impersonator-of? sub1 imp-vector))

(assert (not (impersonator-of? test-vector chp-vector)))
(assert (not (impersonator-of? test-vector imp-vector)))
(assert (impersonator-of? chp-vector test-vector))
(assert (impersonator-of? imp-vector test-vector))
(assert (not (impersonator-of? imp-vector sub1)))
(assert (not (impersonator-of? sub1 imp-vector)))

(printf "~nequality of vectors with impersonators~n")
(printf "(equal? test-vector test-vector) => ~s~n" (equal? test-vector test-vector))
(printf "(equal? test-vector imp-vector)  => ~s~n" (equal? test-vector imp-vector))
(printf "(equal? test-vector chp-vector)  => ~s~n" (equal? test-vector chp-vector))
(printf "(equal? chp-vector test-vector)  => ~s~n" (equal? chp-vector test-vector))

(assert (equal? test-vector test-vector))
(assert (equal? test-vector imp-vector))
(assert (equal? test-vector chp-vector))
(assert (equal? chp-vector test-vector))

(printf "~nimpersonator?/chaperone?~n")
(printf "(chaperone? test-vector)    => ~s = #f~n" (chaperone? test-vector))
(printf "(chaperone? chp-vector)     => ~s = #t~n" (chaperone? chp-vector))
(printf "(chaperone? chp-vector)     => ~s = #f~n" (chaperone? imp-vector))
(printf "(impersonator? test-vector) => ~s = #f~n" (impersonator? test-vector))
(printf "(impersonator? chp-vector)  => ~s = #t~n" (impersonator? chp-vector))
(printf "(impersonator? chp-vector)  => ~s = #t~n" (impersonator? imp-vector))

(assert (not (chaperone? test-vector)))
(assert (chaperone? chp-vector))
(assert (not (chaperone? imp-vector)))
(assert (not (impersonator? test-vector)))
(assert (impersonator? chp-vector))
(assert (impersonator? imp-vector))

(printf "~nchaperone-of? box examples~n")
(printf "test-box ? imp-box  => ~s = #f ~n" (chaperone-of? test-box imp-box))
(printf "imp-box  ? test-box => ~s = #f ~n" (chaperone-of? imp-box test-box))
(printf "chp-box  ? test-box => ~s = #t ~n" (chaperone-of? chp-box test-box))
(printf "test-box ? chp-box  => ~s = #f ~n" (chaperone-of? test-box chp-box))

(assert (not (chaperone-of? test-box imp-box)))
(assert (not (chaperone-of? imp-box test-box)))
(assert (chaperone-of? chp-box test-box))
(assert (not (chaperone-of? test-box chp-box)))

(printf "~nimpersonator-of? box examples~n")
(printf "test-box ? chp-box  => ~s = #f ~n" (impersonator-of? test-box chp-box))
(printf "test-box ? imp-box  => ~s = #f ~n" (impersonator-of? test-box imp-box))
(printf "chp-box  ? test-box => ~s = #t ~n" (impersonator-of? chp-box test-box))
(printf "imp-box  ? test-box => ~s = #t ~n" (impersonator-of? imp-box test-box))
(printf "imp-box  ? sub1     => ~s = #f ~n" (impersonator-of? imp-box sub1))
(printf "sub1     ? imp-box  => ~s = #f ~n" (impersonator-of? sub1 imp-box))

(assert (not (impersonator-of? test-box chp-box)))
(assert (not (impersonator-of? test-box imp-box)))
(assert (impersonator-of? chp-box test-box))
(assert (impersonator-of? imp-box test-box))
(assert (not (impersonator-of? imp-box sub1)))
(assert (not (impersonator-of? sub1 imp-box)))
