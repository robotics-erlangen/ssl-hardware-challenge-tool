import time
from enum import Enum
from aux.utils import red_print, blue_print, green_print, purple_print
from aux.GCSocket import GCCommands

from aux.hw_challenge_1 import Challenge_1
from aux.hw_challenge_2 import Challenge_2
from aux.hw_challenge_3 import Challenge_3
from aux.hw_challenge_4 import Challenge_4

from aux.challenge_aux import ChallengeSteps, ChallengeEvents, Action

ROBOT_STOP_TRESHOLD = 2  # in seconds


class ChallengeFSM(object):
    def __init__(self):
        self.current_step = ChallengeSteps.STEP_0
        self.current_challenge = None
        self.challenge_end_callback = None
        self.current_action = Action()

        # Used when time needs to be counted
        self.dt_cmd = [0, 0]
        self.dt_chl = [0, 0]

    def challenge_external_event(self, event: ChallengeEvents):
        if event == ChallengeEvents.GOAL and self.current_challenge.id in [1, 2] or \
                event == ChallengeEvents.ROBOT_STOPPED and self.current_challenge.id == 3:
            self.proceed_step()

            if self.current_step == ChallengeSteps.STEP_0 and \
                    self.challenge_end_callback != None:
                self.dt_chl[1] = time.time_ns() / 1e9

                # Subtract the time used to consider if the robot stopped
                if event == ChallengeEvents.ROBOT_STOPPED:
                    self.dt_chl[1] = self.dt_chl[1] - ROBOT_STOP_TRESHOLD

                blue_print('Stop challenge timer!')

                self.challenge_end_callback()

    def set_challenge(self, challenge: int):
        self.current_step = ChallengeSteps.STEP_1
        self.dt_chl = [0, 0]

        if not isinstance(challenge, int) or (challenge < 1 or challenge > 4):
            raise ValueError('Challenge ID must be between 1 and 4!')

        if challenge == 1:
            self.current_challenge = Challenge_1
        elif challenge == 2:
            self.current_challenge = Challenge_2
        elif challenge == 3:
            self.current_challenge = Challenge_3
        elif challenge == 4:
            self.current_challenge = Challenge_4

        green_print('[CHALLENGE FSM] Challenge {} set!'.format(challenge))

    def set_end_callback(self, callback_fn=None):
        if callback_fn != None:
            self.challenge_end_callback = callback_fn
            green_print('[CHALLENGE FSM] Callback set!')

    def proceed_step(self):
        next_step = ChallengeSteps.next_step(self.current_step)

        if next_step.value <= self.current_challenge.max_steps:
            self.current_step = next_step
        else:
            self.current_step = ChallengeSteps.STEP_0

    def get_challenge_time(self):
        return self.dt_chl[1] - self.dt_chl[0]

    def get_current_command(self) -> GCCommands:
        action = self.current_challenge.Step(self.current_step)
        timer_ended = False

        if action.timer != 0 and self.dt_cmd == [0, 0]:
            self.dt_cmd[0] = time.time_ns() / 1e9
            self.dt_cmd[1] = time.time_ns() / 1e9

        elif action.timer != 0 and self.dt_cmd[0] > 0:
            self.dt_cmd[1] = time.time_ns() / 1e9

            dt = self.dt_cmd[1] - self.dt_cmd[0]
            print('Challenge time = {:.2f}/{} s'.format(dt, action.timer),
                  end='\r')

            if dt >= action.timer:
                timer_ended = True
                self.dt_cmd = [0, 0]

        if action.command != GCCommands.NONE or timer_ended:
            if action.start_timer and self.dt_chl[0] == 0:
                self.dt_chl[0] = time.time_ns() / 1e9
                blue_print('Starting challenge timer...')

            self.proceed_step()

            if self.current_step == ChallengeSteps.STEP_0 and \
                    self.challenge_end_callback != None:
                self.dt_chl[1] = time.time_ns() / 1e9
                blue_print('\nStop challenge timer!')

                self.challenge_end_callback()

        return action.command
