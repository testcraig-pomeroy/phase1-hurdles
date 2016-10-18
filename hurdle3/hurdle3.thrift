
/**
 * Thrift file for Hurdle 3
 */
namespace cpp hurdle3_rpc
namespace py hurdle3_rpc

struct StepResult {
    1: required i32 predicted_state;
    2: required i32 next_state;
}



/**
 * Set up Hurdle 3 namespace
 */
service Hurdle3Execution {

  /**
   * trigger first iteration of participant state machine.
   * Note that start() should initialize the solution for
   * the beginning of a test, even if called in the middle of a 
   * test, in order to support running multiple consecutive trials.
   */
    StepResult start()

  /**
   * trigger subsequent participant state machine
   * input is a pair of integers: the reward for the last iteration
   * and the state machine's observed state from the last iteration. 
   * The return is an integer pair: the predicted next state for the
   * state machine and the choice of next state
   */
    StepResult step(1:i32 reward, 2:i32 observation)

  /*
   * Shut down hurdle3
   */   
    oneway void stop()

}
