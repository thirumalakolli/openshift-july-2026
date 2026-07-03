package org.tektutor;

import javax.jms.*;
import org.apache.activemq.artemis.jms.client.ActiveMQConnectionFactory;

public class JmsConsumer {
    public static void main(String[] args) throws Exception {
	// Use fully qualified service name for cross-namespace communication
	String brokerUrl = "tcp://amq-broker-core-0-svc.jms-demo.svc.cluster.local:61616";
        String user = System.getenv("AMQ_USER");
        String password = System.getenv("AMQ_PASSWORD");

        // Fallback to hardcoded values if env vars not set
        if (user == null) user = "gsFZ8w5b";
        if (password == null) password = "DtLY5U1h";

        // For local testing, use localhost
        // String brokerUrl = "tcp://localhost:61616";

        try (ActiveMQConnectionFactory cf = new ActiveMQConnectionFactory(brokerUrl, user, password);
             JMSContext context = cf.createContext()) {
            
            Queue queue = context.createQueue("order.queue");
            JMSConsumer consumer = context.createConsumer(queue);
            
            System.out.println("Waiting for messages... Press Ctrl+C to exit");
            
            // Receive messages continuously
            while (true) {
                Message message = consumer.receive(5000); // 5 second timeout
                
                if (message != null) {
                    if (message instanceof TextMessage) {
                        TextMessage textMessage = (TextMessage) message;
                        System.out.println("Received message: " + textMessage.getText());
                        System.out.println("Message ID: " + message.getJMSMessageID());
                        System.out.println("Timestamp: " + message.getJMSTimestamp());
                        System.out.println("---");
                    } else {
                        System.out.println("Received non-text message: " + message);
                    }
                } else {
                    System.out.println("No message received in 5 seconds...");
                }
            }
        } catch (JMSException e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace();
        }
    }
}
