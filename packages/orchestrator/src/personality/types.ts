/**
 * HEXACO Personality Model
 *
 * 6 domains, 24 facets total (4 facets per domain).
 * Each facet is scored from 0.0 (low) to 1.0 (high).
 */
export interface HexacoFacets {
  // Honesty-Humility (H)
  sincerity: number;
  fairness: number;
  greedAvoidance: number;
  modesty: number;

  // Emotionality (E)
  fearfulness: number;
  anxiety: number;
  dependence: number;
  sentimentality: number;

  // Extraversion (X)
  socialSelfEsteem: number;
  socialBoldness: number;
  sociability: number;
  liveliness: number;

  // Agreeableness (A)
  forgivingness: number;
  gentleness: number;
  flexibility: number;
  patience: number;

  // Conscientiousness (C)
  organization: number;
  diligence: number;
  perfectionism: number;
  prudence: number;

  // Openness to Experience (O)
  aestheticAppreciation: number;
  inquisitiveness: number;
  creativity: number;
  unconventionality: number;
}

/**
 * TCI-R Temperament dimensions (biologically based, stable).
 */
export interface TciTemperament {
  // Novelty Seeking (NS) - associated with dopamine
  exploratoryExcitability: number;
  impulsiveness: number;
  extravagance: number;
  disorderliness: number;

  // Harm Avoidance (HA) - associated with serotonin
  anticipatoryWorry: number;
  fearOfUncertainty: number;
  shyness: number;
  fatigability: number;

  // Reward Dependence (RD)
  sentimentality: number;
  opennessToWarmCommunication: number;
  attachment: number;
  dependence: number;

  // Persistence (PS)
  eagernessOfEffort: number;
  workHardened: number;
  ambitious: number;
  perfectionist: number;
}

/**
 * TCI-R Character dimensions (learned, evolves over time).
 */
export interface TciCharacter {
  // Self-Directedness (SD)
  responsibility: number;
  purposefulness: number;
  resourcefulness: number;
  selfAcceptance: number;
  congruence: number;

  // Cooperativeness (C)
  socialAcceptance: number;
  empathy: number;
  helpfulness: number;
  compassion: number;
  pureConsciousness: number;

  // Self-Transcendence (ST)
  selfForgetfulness: number;
  transpersonalIdentification: number;
  spiritualAcceptance: number;
}

/**
 * Schwartz's 19 refined basic human values.
 * Each value is scored from 0.0 (not valued) to 1.0 (highly valued).
 */
export interface SchwartzValues {
  selfDirectionThought: number;
  selfDirectionAction: number;
  stimulation: number;
  hedonism: number;
  achievement: number;
  powerDominance: number;
  powerResources: number;
  face: number;
  securityPersonal: number;
  securitySocietal: number;
  tradition: number;
  conformityRules: number;
  conformityInterpersonal: number;
  humility: number;
  benevolenceDependability: number;
  benevolenceCaring: number;
  universalismConcern: number;
  universalismNature: number;
  universalismTolerance: number;
}

/**
 * Piaget's cognitive development stages.
 */
export type CognitiveStage =
  | 'sensorimotor'
  | 'preoperational'
  | 'concrete_operational'
  | 'formal_operational';

/**
 * The complete personality state of a Ser at a given point in time.
 */
export interface PersonalityState {
  hexaco: HexacoFacets;
  temperament: TciTemperament;
  character: TciCharacter;
  values: SchwartzValues;
  cognitiveStage: CognitiveStage;
  cognitiveAge: number; // interaction count as proxy for development
}

/**
 * Creates a blank tabula rasa personality state.
 * All values start at 0.5 (neutral midpoint) for traits,
 * and 0.0 for values (nothing valued yet).
 */
export function createTabulaRasa(): PersonalityState {
  return {
    hexaco: {
      sincerity: 0.5,
      fairness: 0.5,
      greedAvoidance: 0.5,
      modesty: 0.5,
      fearfulness: 0.5,
      anxiety: 0.5,
      dependence: 0.5,
      sentimentality: 0.5,
      socialSelfEsteem: 0.5,
      socialBoldness: 0.5,
      sociability: 0.5,
      liveliness: 0.5,
      forgivingness: 0.5,
      gentleness: 0.5,
      flexibility: 0.5,
      patience: 0.5,
      organization: 0.5,
      diligence: 0.5,
      perfectionism: 0.5,
      prudence: 0.5,
      aestheticAppreciation: 0.5,
      inquisitiveness: 0.5,
      creativity: 0.5,
      unconventionality: 0.5,
    },
    temperament: {
      exploratoryExcitability: 0.5,
      impulsiveness: 0.5,
      extravagance: 0.5,
      disorderliness: 0.5,
      anticipatoryWorry: 0.5,
      fearOfUncertainty: 0.5,
      shyness: 0.5,
      fatigability: 0.5,
      sentimentality: 0.5,
      opennessToWarmCommunication: 0.5,
      attachment: 0.5,
      dependence: 0.5,
      eagernessOfEffort: 0.5,
      workHardened: 0.5,
      ambitious: 0.5,
      perfectionist: 0.5,
    },
    character: {
      responsibility: 0.0,
      purposefulness: 0.0,
      resourcefulness: 0.0,
      selfAcceptance: 0.0,
      congruence: 0.0,
      socialAcceptance: 0.0,
      empathy: 0.0,
      helpfulness: 0.0,
      compassion: 0.0,
      pureConsciousness: 0.0,
      selfForgetfulness: 0.0,
      transpersonalIdentification: 0.0,
      spiritualAcceptance: 0.0,
    },
    values: {
      selfDirectionThought: 0.0,
      selfDirectionAction: 0.0,
      stimulation: 0.0,
      hedonism: 0.0,
      achievement: 0.0,
      powerDominance: 0.0,
      powerResources: 0.0,
      face: 0.0,
      securityPersonal: 0.0,
      securitySocietal: 0.0,
      tradition: 0.0,
      conformityRules: 0.0,
      conformityInterpersonal: 0.0,
      humility: 0.0,
      benevolenceDependability: 0.0,
      benevolenceCaring: 0.0,
      universalismConcern: 0.0,
      universalismNature: 0.0,
      universalismTolerance: 0.0,
    },
    cognitiveStage: 'sensorimotor',
    cognitiveAge: 0,
  };
}
