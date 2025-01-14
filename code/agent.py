import numpy as np
from scipy import stats # for gaussian noise
from environment import Environment

class DynaAgent(Environment):

    def __init__(self, alpha, gamma, epsilon):

        '''
        Initialise the agent class instance
        Input arguments:
            alpha   -- learning rate \in (0, 1]
            gamma   -- discount factor \in (0, 1)
            epsilon -- controls the influence of the exploration bonus
        '''

        self.alpha   = alpha
        self.gamma   = gamma 
        self.epsilon = epsilon

        return None

    def init_env(self, **env_config):

        '''
        Initialise the environment
        Input arguments:
            **env_config -- dictionary with environment parameters
        '''

        Environment.__init__(self, **env_config)

        return None

    def _init_q_values(self):

        '''
        Initialise the Q-value table
        '''

        self.Q = np.zeros((self.num_states, self.num_actions))

        return None

    def _init_experience_buffer(self):

        '''
        Initialise the experience buffer
        '''

        self.experience_buffer = np.zeros((self.num_states*self.num_actions, 4), dtype=int)
        for s in range(self.num_states):
            for a in range(self.num_actions):
                self.experience_buffer[s*self.num_actions+a] = [s, a, 0, s]

        return None

    def _init_history(self):

        '''
        Initialise the history
        '''

        self.history = np.empty((0, 4), dtype=int)

        return None
    
    def _init_action_count(self):

        '''
        Initialise the action count
        '''

        self.action_count = np.zeros((self.num_states, self.num_actions), dtype=int)

        return None

    def _init_action_taken(self):

        #1 = action taken, 0 = action not taken yet

        self.action_taken = np.zeros(np.shape(self.action_count))

    def _update_experience_buffer(self, s, a, r, s1):

        '''
        Update the experience buffer (world model)
        Input arguments:
            s  -- initial state
            a  -- chosen action         
            r  -- received reward
            s1 -- next state
        '''

        self.experience_buffer[s*self.num_actions+a] = [s,a,r,s1]

        return None

    def _update_qvals(self, s, a, r, s1, bonus=False):

        '''
        Update the Q-value table
        Input arguments:
            s     -- initial state
            a     -- chosen action
            r     -- received reward
            s1    -- next state
            bonus -- True / False whether to use exploration bonus or not
        '''

        self.Q[s,a] += self.alpha*(r+self.gamma*np.max(self.Q[s1])-self.Q[s,a])

        if bonus == True:
            self.Q[s,a] += self.alpha*(r+self.epsilon*np.sqrt(self.action_count[s,a])+self.gamma*np.max(self.Q[s1])-self.Q[s,a])

        return None

    def _update_action_count(self, s, a):

        '''
        Update the action count
        Input arguments:
            Input arguments:
            s  -- initial state
            a  -- chosen action
        '''
        self.action_count += 1
        self.action_count[s,a] = 0

        '''

        if self.action_taken[s,a] == 0:
            self.action_taken[s,a] = 1
        for states in range(np.shape(self.action_taken)[0]):
            for actions in range(np.shape(self.action_taken)[1]):
                if self.action_taken[states,actions] == 1:
                    self.action_count[states,actions] = self.action_count[states,actions] + 1
                    self.action_count[s,a] = 0
        '''

        return None

    def _update_history(self, s, a, r, s1):

        '''
        Update the history
        Input arguments:
            s     -- initial state
            a     -- chosen action
            r     -- received reward
            s1    -- next state
        '''

        self.history = np.vstack((self.history, np.array([s, a, r, s1])))

        return None

    def _policy(self, s):

        '''
        Agent's policy 
        Input arguments:
            s -- state
        Output:
            a -- index of action to be chosen
        '''
        
        if np.all(np.unique(self.Q[s])==self.Q[s,0]):
            a = np.random.choice(len(self.Q[s]))
        else:
            a = np.argmax(self.Q[s]) 

        return a

    def _plan(self, num_planning_updates):

        '''
        Planning computations
        Input arguments:
            num_planning_updates -- number of planning updates to execute
        '''
        for _ in range(num_planning_updates):
            mod = np.random.randint(self.experience_buffer.shape[0])
            s,a,r,s1 = self.experience_buffer[mod]
            self._update_qvals(s, a, r, s1, bonus=True)
        
        '''
        s = np.random.randint(self.num_states)

        for i in range(num_planning_updates):
            a = self._policy(s)
            _, _, r, s1= self.experience_buffer[s*self.num_actions+a]
            self._update_qvals(s, a, r, s1, bonus=True)
            s = s1 
         '''       

        return None

    def get_performace(self):

        '''
        Returns cumulative reward collected prior to each move
        '''

        return np.cumsum(self.history[:, 2])

    def simulate(self, num_trials, reset_agent=True, num_planning_updates=None):

        '''
        Main simulation function
        Input arguments:
            num_trials           -- number of trials (i.e., moves) to simulate
            reset_agent          -- whether to reset all knowledge and begin at the start state
            num_planning_updates -- number of planning updates to execute after every move
        '''

        if reset_agent:
            self._init_q_values()
            self._init_experience_buffer()
            self._init_action_count()
            self._init_history()
            self._init_action_taken()

            self.s = self.start_state

        for _ in range(num_trials):

            # choose action
            a  = self._policy(self.s)
            # get new state
            s1 = np.random.choice(np.arange(self.num_states), p=(self.T[self.s, a, :]))
            # receive reward
            r  = self.R[self.s, a]
            # learning
            self._update_qvals(self.s, a, r, s1, bonus=False)
            # update world model 
            self._update_experience_buffer(self.s, a, r, s1)
            # reset action count
            self._update_action_count(self.s, a)
            # update history
            self._update_history(self.s, a, r, s1)
            # plan
            if num_planning_updates is not None:
                self._plan(num_planning_updates)

            if s1 == self.goal_state:
                self.s = self.start_state
            else:
                self.s = s1

        return None
    
class TwoStepAgent:

    def __init__(self, alpha1, alpha2, beta1, beta2, lam, w, p):

        '''
        Initialise the agent class instance
        Input arguments:
            alpha1 -- learning rate for the first stage \in (0, 1]
            alpha2 -- learning rate for the second stage \in (0, 1]
            beta1  -- inverse temperature for the first stage
            beta2  -- inverse temperature for the second stage
            lam    -- eligibility trace parameter
            w      -- mixing weight for MF vs MB \in [0, 1] 
            p      -- perseveration strength
        '''

        self.alpha1 = alpha1
        self.alpha2 = alpha2
        self.beta1  = beta1
        self.beta2  = beta2
        self.lam    = lam
        self.w      = w
        self.p      = p

        return None
    
    def _init_env(self):
        #Initialise environment
        self.num_actions = 2
        self.num_states = 3
        self.start = 0
        return None
        
    def _init_q(self): # NET Q values
        num_actions = 2
        num_states = 3
        self.q = np.zeros((num_states,num_actions))
        return None 
    
    def _init_model_tran(self): #Middle transition to be learned
        self.model_tran = np.array([[0.7, 0.3],[0.3, 0.7]])

    def _init_tran_mat(self): #Transition matrix for the ones we can actually pick
        self.tran_mat = np.ones((2,2))*0.5
        return None
    
    def update_trans_mat(self,s1,a): #Softmax
        self.tran_mat[s1,a] = np.exp(self.)

    def _init_actions(self):
        self.actions = np.random.randint(2, size=3) #3 actions

    def _init_rewards(self):
        self.rewards = np.random.uniform(0.25,0.75,4)

        return None
    
    def update_rewards(self):
        noise = np.random.normal(0,0.025)
        for r in self.rewards:
            if r > 0.75:
                r -= np.absolute(noise)
            elif r < 0.25:
                r += np.absolute(noise)
            else:
                r += noise
    
    def _init_qtd(self): #model free q 
        num_actions = 2
        num_states = 3
        self.qtd = np.zeros((num_states,num_actions))

        return None

    def update_qtd(self):
        #Find Q1
        delta = self.qtd[1,self.actions[1]] - self.qtd[0,self.actions[0]] #R is 0 here
        self.qtd[0,self.actions[0]] += self.alpha1*delta

        #Find Q2 
        delta2 = self.rewards - self.qtd[1,self.actions[1]]
        self.qtd[1,self.actions[1]] += self.alpha2*delta2
    
        #Eligibility trace
        self.qtd[0,self.actions[0]] += self.alpha1 * self.lam * delta2

    def _init_qmb(self):
        num_actions = 2
        num_states = 3
        self.qmb = np.zeros((num_states,num_actions))

        return None

    def update_qmb(self,a):
        #Q_mb = Q_td at stage 2 
        self.qmb[1] = self.qtd[1]
        self.qmb[0,a] = self.model_tran[a,0] * np.max(self.qtd[1]) + self.model_tran[a,1] * np.max(self.qtd[2]) 

        return None
        


    def _init_history(self):

        '''
        Initialise history to later compute stay probabilities
        '''

        self.history = np.empty((0, 3), dtype=int)

        return None
    
    def _update_history(self, a, s1, r1):

        '''
        Update history
        Input arguments:
            a  -- first stage action
            s1 -- second stage state
            r1 -- second stage reward
        '''

        self.history = np.vstack((self.history, [a, s1, r1]))

        return None
    
    def get_stay_probabilities(self):

        '''
        Calculate stay probabilities
        '''

        common_r      = 0
        num_common_r  = 0
        common_nr     = 0
        num_common_nr = 0
        rare_r        = 0
        num_rare_r    = 0
        rare_nr       = 0
        num_rare_nr   = 0

        num_trials = self.history.shape[0]
        for idx_trial in range(num_trials-1):
            a, s1, r1 = self.history[idx_trial, :]
            a_next    = self.history[idx_trial+1, 0]

            # common
            if (a == 0 and s1 == 1) or (a == 1 and s1 == 2):
                # rewarded
                if r1 == 1:
                    if a == a_next:
                        common_r += 1
                    num_common_r += 1
                else:
                    if a == a_next:
                        common_nr += 1
                    num_common_nr += 1
            else:
                if r1 == 1:
                    if a == a_next:
                        rare_r += 1
                    num_rare_r += 1
                else:
                    if a == a_next:
                        rare_nr += 1
                    num_rare_nr += 1

        return np.array([common_r/num_common_r, rare_r/num_rare_r, common_nr/num_common_nr, rare_nr/num_rare_nr])

    def simulate(self, num_trials):

        '''
        Main simulation function
        Input arguments:
            num_trials -- number of trials to simulate
        '''
            
        # complete the code

        return None