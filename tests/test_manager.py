import copy
import numpy as np
import paho.mqtt.client as mqtt
from unittest import TestCase
from NoveltyProducer.Manager import Manager, InvalidInputTypeError, InvalidInputValueError
from NoveltyProducer.Generator import Generator
from NoveltyProducer.Technican import Technican
from apscheduler.job import Job

ip = 'test.mosquitto.org'
# ip = 'localhost' 
port = 1883
topic = 'foo'
frequency = 1
channel_name = 'bar'
channel_limits = [-2, 2]
channel_frequency = 0.1
pipeline_name = 'pipe'
type = 'sin'
dead_frequency = 1
dead_period = 0

class TestBaseUnit(TestCase):

    def test_value_output(self):
        """Test output of each function."""
        
        # init instance of Manager
        man = Manager()
        
        # _add_connection
        con_id = man._add_connection(ip_=ip, port_=port)
        self.assertEqual(ip, man.connections[con_id]['ip'])
        self.assertEqual(port, man.connections[con_id]['port'])
        
        # _add_topic
        top_id = man._add_topic(topic_=topic, frequency_=frequency)
        self.assertEqual(topic, man.topics[top_id]['topic'])
        self.assertEqual(frequency, man.topics[top_id]['frequency'])
        
        # _add_channel
        chn_id = man._add_channel(name_=channel_name, limits_=channel_limits, frequency_=channel_frequency,
                                  type_=type, dead_frequency_=dead_frequency, dead_period_=dead_period)
        self.assertEqual(channel_name, man.channels[chn_id]['name'])
        self.assertEqual(channel_limits, man.channels[chn_id]['limits'])
        self.assertEqual(channel_frequency, man.channels[chn_id]['frequency'])
        self.assertEqual(type, man.channels[chn_id]['type'])
        self.assertEqual(dead_frequency, man.channels[chn_id]['dead_frequency'])
        self.assertEqual(dead_period, man.channels[chn_id]['dead_period'])
        
        # _add_pipeline
        pipe_id = man._add_pipeline(name_=pipeline_name, host_id_=con_id, topic_id_=top_id, channel_id_=chn_id)
        self.assertEqual(pipeline_name, man.pipelines[pipe_id]['name'])
        self.assertEqual(con_id, man.pipelines[pipe_id]['host_id'])
        self.assertEqual(top_id, man.pipelines[pipe_id]['topic_id'])
        self.assertIn(chn_id, man.pipelines[pipe_id]['channel_id'])
        self.assertEqual(1, man.pipelines[pipe_id]['active'])
        
        # switch_pipeline (on to off)
        pipeline_status = man.pipelines[pipe_id]['active']
        man.switch_pipeline(pipe_id)
        self.assertTrue(pipeline_status != man.pipelines[pipe_id]['active'])
        
        # switch_pipeline (off to on)
        pipeline_status = man.pipelines[pipe_id]['active']
        man.switch_pipeline(pipe_id)
        self.assertTrue(pipeline_status != man.pipelines[pipe_id]['active'])
        
        # add_channel_to_pipeline
        man.add_channel_to_pipeline(pipe_id, channel_name + '_2')
        self.assertEqual([chn_id, chn_id+1], man.pipelines[pipe_id]['channel_id'])
        self.assertEqual(1, man.pipelines[pipe_id]['active'])
        
        # remove_channel_from_pipeline
        man.remove_channel_from_pipeline(chn_id)
        self.assertNotIn(chn_id, man.channels.keys())
        
        # publish_data
        (rc, mid) = man.publish_data(pipe_id)
        self.assertTrue(rc == 0)
        self.assertTrue(mid >= 0)        
        
    def test_type_output(self):
        """Test types of output"""
        
        # init instance of Manager
        man = Manager()
        
        # _add_connection
        con_id = man._add_connection(ip_=ip, port_=port)
        self.assertIsInstance(con_id, int)
        
        # _add_topic
        top_id = man._add_topic(topic_=topic, frequency_=frequency)
        self.assertIsInstance(top_id, int)
        
        # _add_channel
        chn_id = man._add_channel(name_=channel_name, limits_=channel_limits, frequency_=channel_frequency)
        self.assertIsInstance(chn_id, int)
        
        # _add_pipeline
        pipe_id = man._add_pipeline(name_='pipe', host_id_=con_id, topic_id_=top_id, channel_id_=chn_id)
        self.assertIsInstance(pipe_id, int)
        
        # _add_handlers
        man._add_handlers(pipe_id)
        self.assertIsInstance(man.handlers[pipe_id]['technican'], Technican)
        self.assertIsInstance(man.handlers[pipe_id]['mqtt'], mqtt.Client)
        
        # create_pipeline
        man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, pipeline_name_=pipeline_name)
        pipe_id = [k for k,v in man.pipelines.items() if man.pipelines[k]['name'] == pipeline_name][0]
        self.assertIsInstance(man.Scheduler.get_job(str(pipe_id)), Job)
        
        # publish_data
        info = man.publish_data(pipe_id)
        self.assertIsInstance(info, mqtt.MQTTMessageInfo)
                
    def test_invalid_inputs(self):
        """Test for all expected errors that should be raised when given invalid inputs"""
        
        # init instance of Manager
        man = Manager()
        
        # ip_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=127001, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name)
        
        # port_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_='1883', topic_=topic, frequency_=frequency, channel_name_=channel_name)
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=65536, topic_=topic, frequency_=frequency, channel_name_=channel_name)
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=-1, topic_=topic, frequency_=frequency, channel_name_=channel_name)
            
        # topic_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=42, frequency_=frequency, channel_name_=channel_name)

        # frequency_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_='1', channel_name_=channel_name)
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=0, channel_name_=channel_name)
            
        # channel_name_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=42)

        # channel_limits_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, channel_limits_=42)
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, channel_limits_=['-12.3', 13.5])
            
        # channel_frequency_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, channel_frequency_='42')
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, channel_frequency_=0)

        # dead_frequency_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, dead_frequency_='42')
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, dead_frequency_=0)
            
        # dead_period_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, dead_period_='42')
        with self.assertRaises(InvalidInputValueError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, dead_period_=-42)

        # pipeline_name_
        with self.assertRaises(InvalidInputTypeError):
            invalid_generator = man.create_pipeline(ip_=ip, port_=port, topic_=topic, frequency_=frequency, channel_name_=channel_name, pipeline_name_=42)